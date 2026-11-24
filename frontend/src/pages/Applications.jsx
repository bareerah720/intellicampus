
import { useState, useEffect } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import {
  fetchApplicationSetup,
  fetchMyApplications,
  submitApplication,
  fetchApplicationTracking,
  resubmitApplication,
  fetchApplicationAttachments,
  uploadApplicationAttachment,
  fetchApplicationComments,
  createApplicationComment,
} from '../services/applicationService'

function getStatusClass(status) {
  const normalized = (status || 'submitted')
    .toLowerCase()
    .replaceAll(' ', '_')

  return `status-chip ${normalized}`
}

function formatStatus(status) {
  return (status || 'submitted')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatApplication(app) {
  return {
    id: app.id,
    trackingNumber: app.tracking_number,
    type: app.application_type_name,
    applicationTypeId: app.application_type,
    date: app.submitted_at
      ? new Date(app.submitted_at).toLocaleDateString()
      : '',
    status: app.status,
    currentStep: app.current_step_name || 'Not assigned yet',
    data: app.form_data || {},
    comments: [],
    attachments: [],
  }
}

function Applications() {
  const { user } = useAuth()

  const role = user?.user_type || 'student'

  // Application setup states
  const [requestTypes, setRequestTypes] = useState([])
  const [loadingTypes, setLoadingTypes] = useState(true)
  const [apiError, setApiError] = useState('')

  // Application list states
  const [applications, setApplications] = useState([])
  const [loadingApplications, setLoadingApplications] = useState(true)

  // Form and detail states
  const [selected, setSelected] = useState(null)
  const [selectedApplication, setSelectedApplication] = useState(null)
  const [formData, setFormData] = useState({})
  const [commentText, setCommentText] = useState('')
  const [attachmentFile, setAttachmentFile] = useState(null)
  const [notice, setNotice] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Revision and tracking states
  const [editingApplication, setEditingApplication] = useState(null)
  const [trackingHistory, setTrackingHistory] = useState([])
  const [loadingTracking, setLoadingTracking] = useState(false)
  const [currentOfficer, setCurrentOfficer] = useState(null)
  const [fieldFiles, setFieldFiles] = useState({})
  const [existingAttachments, setExistingAttachments] = useState([])
  const [savingCommunication, setSavingCommunication] = useState(false)

  // Load application types and dynamic fields
  useEffect(() => {
    async function loadApplicationSetup() {
      try {
        setLoadingTypes(true)
        setApiError('')

        const types = await fetchApplicationSetup()
        setRequestTypes(types)
      } catch (error) {
        console.error('Application setup error:', error)

        setApiError(
          error.response?.data?.detail ||
          'Unable to load application types. Please try again.'
        )
      } finally {
        setLoadingTypes(false)
      }
    }

    loadApplicationSetup()
  }, [])

  // Load student's applications
  useEffect(() => {
    async function loadApplications() {
      try {
        setLoadingApplications(true)

        const data = await fetchMyApplications()

        const formattedApplications = (Array.isArray(data) ? data : data?.results || []).map(formatApplication)

        setApplications(formattedApplications)
      } catch (error) {
        console.error('My applications error:', error)
        setNotice('Unable to load your applications.')
      } finally {
        setLoadingApplications(false)
      }
    }

    loadApplications()
  }, [])

  // Load tracking history when application details are opened
  useEffect(() => {
    if (!selectedApplication?.id) {
      setTrackingHistory([])
      return
    }

    let isActive = true

    async function loadTracking() {
      try {
        setLoadingTracking(true)
        const [tracking, attachments, comments] = await Promise.all([
          fetchApplicationTracking(selectedApplication.id),
          fetchApplicationAttachments(selectedApplication.id),
          fetchApplicationComments(selectedApplication.id),
        ])

        if (isActive) {
          setTrackingHistory(tracking.history || [])
          setCurrentOfficer(tracking.current_officer || null)
          setSelectedApplication((current) => current?.id === selectedApplication.id
            ? { ...current, attachments, comments }
            : current)
        }
      } catch (error) {
        console.error('Application tracking error:', error)

        if (isActive) {
          setTrackingHistory([])
          setCurrentOfficer(null)
        }
      } finally {
        if (isActive) {
          setLoadingTracking(false)
        }
      }
    }

    loadTracking()

    return () => {
      isActive = false
    }
  }, [selectedApplication?.id])

  // Update application list and selected detail
  function saveApplications(updated) {
    setApplications(updated)

    if (selectedApplication) {
      const refreshed = updated.find(
        (app) => app.id === selectedApplication.id
      )

      setSelectedApplication(refreshed || null)
    }
  }

  // Update dynamic form fields
  function updateField(fieldName, value) {
    setFormData((previous) => ({
      ...previous,
      [fieldName]: value,
    }))
  }

  // Submit new application or resubmit a revised application
  async function handleSubmit(e) {
    e.preventDefault()

    if (!selected || submitting) return

    try {
      setSubmitting(true)
      setNotice('')

      const applicationData = {
        title: selected.name,
        form_data: formData,
      }

      // Revision resubmission
      if (editingApplication) {
        const missingRequiredFiles = selected.fields.filter(
          (field) => field.field_type === 'file'
            && field.is_required
            && !fieldFiles[field.field_name]
            && existingAttachments.length === 0
        )
        if (missingRequiredFiles.length) {
          setNotice(`Upload required file(s): ${missingRequiredFiles.map((field) => field.label).join(', ')}.`)
          return
        }

        const resubmissionData = { ...applicationData }

        // The backend rejects a blank description, so only send it when non-empty.
        if (selected.description?.trim()) {
          resubmissionData.description = selected.description
        }

        await resubmitApplication(
          editingApplication.id,
          resubmissionData
        )

        const uploadResults = await Promise.allSettled(
          Object.values(fieldFiles).map((file) =>
            uploadApplicationAttachment(editingApplication.id, file)
          )
        )

        const data = await fetchMyApplications()
        const formattedApplications = (Array.isArray(data) ? data : data?.results || []).map(formatApplication)

        setApplications(formattedApplications)
        setSelectedApplication(null)
        setEditingApplication(null)
        setSelected(null)
        setFormData({})
        setFieldFiles({})
        setExistingAttachments([])

        setNotice(uploadResults.some((result) => result.status === 'rejected')
          ? `Application ${editingApplication.trackingNumber} was resubmitted, but an attachment upload failed.`
          : `Application ${editingApplication.trackingNumber} resubmitted successfully!`)

      } else {
        const missingRequiredFiles = selected.fields.filter(
          (field) => field.field_type === 'file' && field.is_required && !fieldFiles[field.field_name]
        )
        if (missingRequiredFiles.length) {
          setNotice(`Upload required file(s): ${missingRequiredFiles.map((field) => field.label).join(', ')}.`)
          return
        }

        // New application submission
        const savedApplication = await submitApplication({
          application_type: selected.id,
          title: selected.name,
          description: selected.description || '',
          form_data: formData,
        })

        const uploadResults = await Promise.allSettled(
          Object.values(fieldFiles).map((file) =>
            uploadApplicationAttachment(savedApplication.id, file)
          )
        )

        const newApplication = {
          id: savedApplication.id,
          trackingNumber: savedApplication.tracking_number,
          type: savedApplication.application_type_name,
          applicationTypeId: savedApplication.application_type,
          date: savedApplication.submitted_at
            ? new Date(savedApplication.submitted_at).toLocaleDateString()
            : new Date().toLocaleDateString(),
          status: savedApplication.status,
          currentStep: savedApplication.current_step_name || 'Not assigned yet',
          data: savedApplication.form_data || {},
          comments: [],
          attachments: uploadResults
            .filter((result) => result.status === 'fulfilled')
            .map((result) => result.value),
        }

        setApplications((previous) => [
          newApplication,
          ...previous,
        ])

        setSelected(null)
        setFormData({})
        setFieldFiles({})
        setExistingAttachments([])

        const failedUploads = uploadResults.some((result) => result.status === 'rejected')
        setNotice(failedUploads
          ? `Application ${savedApplication.tracking_number} was submitted, but an attachment upload failed. Open the application and retry the missing file.`
          : `Application submitted successfully! Tracking Number: ${savedApplication.tracking_number}`)
      }

    } catch (error) {
      console.error('Application submission error:', error)

      const errorData = error.response?.data

      setNotice(
        typeof errorData === 'object'
          ? JSON.stringify(errorData)
          : 'Application submission failed. Please try again.'
      )
    } finally {
      setSubmitting(false)
    }
  }

    // Open an existing application for revision
  function handleEditAndResubmit(application) {
    const applicationType = requestTypes.find(
      (type) => type.id === application.applicationTypeId
    )

    if (!applicationType) {
      setNotice('Application type could not be found.')
      return
    }

    setEditingApplication(application)
    setSelected(applicationType)
    setFormData(application.data || {})
    setExistingAttachments(application.attachments || [])
    setFieldFiles({})
    setSelectedApplication(null)
    setNotice('')
  }

  function handleBack() {
    setSelected(null)
    setSelectedApplication(null)
    setEditingApplication(null)
    setFormData({})
    setCommentText('')
    setAttachmentFile(null)
    setFieldFiles({})
    setExistingAttachments([])
  }

  async function addComment(e) {
    e.preventDefault()

    if (!commentText.trim() || !selectedApplication) return
    try {
      setSavingCommunication(true)
      const created = await createApplicationComment(selectedApplication.id, commentText.trim())
      setSelectedApplication((current) => ({
        ...current,
        comments: [...(current.comments || []), created],
      }))
      setCommentText('')
      setNotice('Comment added.')
    } catch (error) {
      setNotice(error.response?.data?.detail || 'Could not add comment.')
    } finally {
      setSavingCommunication(false)
    }
  }

  async function addAttachment(e) {
    e.preventDefault()

    if (!attachmentFile || !selectedApplication) return
    try {
      setSavingCommunication(true)
      const created = await uploadApplicationAttachment(selectedApplication.id, attachmentFile)
      setSelectedApplication((current) => ({
        ...current,
        attachments: [...(current.attachments || []), created],
      }))
      setAttachmentFile(null)
      e.target.reset()
      setNotice('Attachment uploaded.')
    } catch (error) {
      setNotice(error.response?.data?.detail || 'Could not upload attachment.')
    } finally {
      setSavingCommunication(false)
    }
  }

  // Render database-driven form fields
  function renderField(field) {
    const commonProps = {
      id: field.field_name,
      name: field.field_name,
      required: field.is_required,
      placeholder: field.placeholder || `Enter ${field.label}`,
      value: formData[field.field_name] ?? '',
      onChange: (e) => updateField(field.field_name, e.target.value),
    }

    switch (field.field_type) {
      case 'file':
        return (
          <input
            id={field.field_name}
            name={field.field_name}
            type="file"
            required={field.is_required && existingAttachments.length === 0}
            onChange={(event) => setFieldFiles((previous) => ({
              ...previous,
              [field.field_name]: event.target.files?.[0] || null,
            }))}
          />
        )
      case 'textarea':
        return <textarea {...commonProps} rows={4} />

      case 'dropdown':
        return (
          <select {...commonProps}>
            <option value="">Select an option</option>

            {(field.options || []).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )

      case 'radio':
        return (
          <div className="dynamic-choice-group">
            {(field.options || []).map((option) => (
              <label key={option.value}>
                <input
                  type="radio"
                  name={field.field_name}
                  value={option.value}
                  required={field.is_required}
                  checked={formData[field.field_name] === option.value}
                  onChange={(e) =>
                    updateField(field.field_name, e.target.value)
                  }
                />
                {option.label}
              </label>
            ))}
          </div>
        )

      case 'checkbox':
        return (
          <div className="dynamic-choice-group">
            {(field.options || []).map((option) => {
              const currentValues = formData[field.field_name] || []
              const checked = currentValues.includes(option.value)

              return (
                <label key={option.value}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => {
                      const nextValues = e.target.checked
                        ? [...currentValues, option.value]
                        : currentValues.filter(
                            (value) => value !== option.value
                          )

                      updateField(field.field_name, nextValues)
                    }}
                  />

                  {option.label}
                </label>
              )
            })}
          </div>
        )

      case 'number':
      case 'email':
      case 'date':
      case 'text':
        return <input {...commonProps} type={field.field_type} />

      default:
        return <input {...commonProps} type="text" />
    }
  }

  return (
    <DashboardLayout role={role}>
      <div className="application-page">

        <div className="page-heading">
          <div>
            <div className="eyebrow">STUDENT SERVICES</div>
            <h1>Application Centre</h1>
            <p>Submit university requests and track their progress.</p>
          </div>
        </div>

        {notice && (
          <div className="application-notice">
            ✓ {notice}
            <button onClick={() => setNotice('')}>×</button>
          </div>
        )}

        {selectedApplication ? (
          <section className="panel application-form-panel">

            <div className="panel-header">
              <div>
                <div className="eyebrow">APPLICATION DETAILS</div>
                <h2>{selectedApplication.type}</h2>
                <p>Application ID: {selectedApplication.id}</p>
              </div>

              <button className="secondary-button" onClick={handleBack}>
                ← Back to Applications
              </button>
            </div>

            <div className="application-list">
              <div className="application-list-item">
                <strong>Tracking Number</strong>
                <span>
                  {selectedApplication.trackingNumber || selectedApplication.id}
                </span>
              </div>

              <div className="application-list-item">
                <strong>Current Workflow Step</strong>
                <span>
                  {selectedApplication.currentStep || 'Not assigned yet'}
                </span>
              </div>

              <div className="application-list-item">
                <strong>Application Date</strong>
                <span>{selectedApplication.date}</span>
              </div>

              <div className="application-list-item">
                <strong>Current Status</strong>
                <span className={getStatusClass(selectedApplication.status)}>
                  {formatStatus(selectedApplication.status)}
                </span>
              </div>

              {currentOfficer && (
                <div className="application-list-item">
                  <strong>Responsible Officer</strong>
                  <span>
                    {currentOfficer.name}
                    {currentOfficer.designation ? ` · ${currentOfficer.designation}` : ''}
                    {currentOfficer.email ? ` · ${currentOfficer.email}` : ''}
                    {currentOfficer.office_email ? ` · ${currentOfficer.office_email}` : ''}
                    {currentOfficer.office_contact_number ? ` · ${currentOfficer.office_contact_number}` : ''}
                    {currentOfficer.office_location ? ` · ${currentOfficer.office_location}` : ''}
                  </span>
                </div>
              )}

              {Object.entries(selectedApplication.data || {}).map(
                ([field, value]) => (
                  <div className="application-list-item" key={field}>
                    <strong>{field.replaceAll('_', ' ')}</strong>
                    <span>
                      {Array.isArray(value)
                        ? value.join(', ')
                        : value || 'Not provided'}
                    </span>
                  </div>
                )
              )}
            </div>

            {selectedApplication.status === 'revision_required' && (
  <div className="revision-required-panel">
    <h3>Correction Required</h3>

    <p>
      Your application has been returned for correction.
      Please review the officer's remarks below and update
      the required information.
    </p>

    <button
      type="button"
      className="primary-button"
      onClick={() => handleEditAndResubmit(selectedApplication)}
    >
      Edit & Resubmit
    </button>
  </div>
)}

            <div className="tracking-history">
  <h3>Application History</h3>

  {loadingTracking ? (
    <p>Loading application history...</p>
  ) : trackingHistory.length === 0 ? (
    <p>No approval history available yet.</p>
  ) : (
    <div className="history-list">
      {trackingHistory.map((item) => (
        <div className="history-item" key={item.id}>
          <strong>{formatStatus(item.action)}</strong>

          <p>
            <strong>Step:</strong> {item.step}
          </p>

          <p>
            <strong>Officer:</strong> {item.action_by}
            {item.designation ? ` (${item.designation})` : ''}
          </p>

          {item.remarks && (
            <div className="revision-remarks">
              <strong>Officer Remarks:</strong>
              <p>{item.remarks}</p>
            </div>
          )}

          <small>
            {item.action_date
              ? new Date(item.action_date).toLocaleString()
              : ''}
          </small>
        </div>
      ))}
    </div>
  )}
</div>

            <div className="communication-section">
              <h3>Supporting Documents</h3>
              <p className="muted-note">Documents are stored with this application.</p>

              {!['approved', 'rejected', 'cancelled'].includes(selectedApplication.status) && <form className="attachment-form" onSubmit={addAttachment}>
                <input
                  type="file"
                  onChange={(e) =>
                    setAttachmentFile(e.target.files?.[0] || null)
                  }
                  required
                />

                <button type="submit" className="primary-button" disabled={savingCommunication}>
                  {savingCommunication ? 'Uploading...' : 'Add Attachment'}
                </button>
              </form>}

              {(selectedApplication.attachments || []).length === 0 ? (
                <p className="empty-communication">
                  No documents attached yet.
                </p>
              ) : (
                <div className="attachment-list">
                  {selectedApplication.attachments.map((file) => (
                    <div className="attachment-item" key={file.id}>
                      <span className="attachment-icon">📎</span>

                      <div>
                        <a href={file.file_path} target="_blank" rel="noreferrer"><strong>{file.file_name}</strong></a>
                        <small>
                          Uploaded by {file.uploaded_by_name || 'User'} · {new Date(file.uploaded_at).toLocaleString()}
                        </small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="communication-section">
              <h3>Application Comments</h3>
              <p className="muted-note">
                Add a comment or follow-up message about your application.
              </p>

              <form className="comment-form" onSubmit={addComment}>
                <textarea
                  rows={3}
                  placeholder="Write your comment here..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  required
                />

                <button
                  type="submit"
                  className="primary-button"
                  disabled={!commentText.trim() || savingCommunication}
                >
                  {savingCommunication ? 'Saving...' : 'Add Comment'}
                </button>
              </form>

              {(selectedApplication.comments || []).length === 0 ? (
                <p className="empty-communication">No comments yet.</p>
              ) : (
                <div className="comment-list">
                  {selectedApplication.comments.map((comment) => (
                    <div className="comment-item" key={comment.id}>
                      <div className="comment-heading">
                        <strong>{comment.user_name || 'User'}</strong>
                        <small>{new Date(comment.created_at).toLocaleString()}</small>
                      </div>

                      <p>{comment.comment}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <p className="muted-note">Comments and attachments are saved to this application record.</p>
          </section>
        ) : selected ? (
          <section className="panel application-form-panel">

            <div className="panel-header">
              <div>
                <div className="eyebrow">
  {editingApplication ? 'EDIT APPLICATION' : 'NEW REQUEST'}
</div>
                                <h2>{selected.name}</h2>
                <p>{selected.description}</p>
              </div>

              <button className="secondary-button" onClick={handleBack}>
                ← Back
              </button>
            </div>

            <form className="form-grid" onSubmit={handleSubmit}>
              {[...selected.fields]
                .sort((a, b) => a.display_order - b.display_order)
                .map((field) => (
                  <label key={field.id}>
                    {field.label}
                    {field.is_required && <span> *</span>}
                    {renderField(field)}
                  </label>
                ))}

              <div className="application-form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleBack}
                  disabled={submitting}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={submitting}
                >
                  {submitting
                    ? 'Submitting...'
                    : editingApplication
                      ? 'Resubmit Application →'
                      : 'Submit Application →'}
                </button>
              </div>
            </form>
          </section>
        ) : (
          <>
            <div className="application-section-heading">
              <div>
                <h2>What would you like to apply for?</h2>
                <p>Select an application type to get started.</p>
              </div>

              <span>{requestTypes.length} Services</span>
            </div>

            {loadingTypes ? (
              <p>Loading application types...</p>
            ) : apiError ? (
              <p className="application-notice">{apiError}</p>
            ) : requestTypes.length === 0 ? (
              <p>No active application types are available.</p>
            ) : (
              <div className="application-type-grid">
                {requestTypes.map((item) => (
                  <button
                    className="application-type-card"
                    key={item.id}
                    onClick={() => {
                      setSelected(item)
                      setNotice('')
                    }}
                  >
                    <span className="application-type-icon">
                      📄
                    </span>

                    <h3>{item.name}</h3>
                    <p>{item.description}</p>

                    <span className="application-card-link">
                      Start application →
                    </span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {!selectedApplication && !selected && (
          <section className="panel my-applications-panel">

            <div className="panel-header">
              <div>
                <h2>My Applications</h2>
                <p>Track the requests you have submitted.</p>
              </div>

              <span className="application-count">
                {applications.length} Total
              </span>
            </div>

            {loadingApplications ? (
              <p>Loading your applications...</p>
            ) : applications.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">▤</div>
                <h3>No applications yet</h3>
                <p>Your submitted requests will appear here.</p>
              </div>
            ) : (
              <div className="application-list">
                {applications.map((app) => (
                  <div className="application-list-item" key={app.id}>
                    <div>
                      <strong>{app.type}</strong>

                      <small>
                        Tracking: {app.trackingNumber || app.id} · {app.date}
                      </small>
                    </div>

                    <div>
                      <span className={getStatusClass(app.status)}>
                        {formatStatus(app.status)}
                      </span>

                      <button
                        className="secondary-button"
                        onClick={() => setSelectedApplication(app)}
                      >
                        View Details →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

      </div>
    </DashboardLayout>
  )
}

export default Applications
