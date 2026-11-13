
import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'

// Demo application types
const requestTypes = [
  {
    id: 1,
    name: 'Leave Request',
    icon: '📅',
    description: 'Apply for academic or medical leave.',
    fields: [
      { id: 1, label: 'Start Date', field_name: 'start_date', field_type: 'date', is_required: true, display_order: 1 },
      { id: 2, label: 'End Date', field_name: 'end_date', field_type: 'date', is_required: true, display_order: 2 },
      { id: 3, label: 'Reason', field_name: 'reason', field_type: 'textarea', is_required: true, display_order: 3 },
    ],
  },
  {
    id: 2,
    name: 'Fee Installment',
    icon: '💳',
    description: 'Request semester fee payment in installments.',
    fields: [
      { id: 4, label: 'Total Fee Due', field_name: 'total_fee', field_type: 'number', is_required: true, display_order: 1 },
      {
        id: 5,
        label: 'Number of Installments',
        field_name: 'installments',
        field_type: 'dropdown',
        is_required: true,
        display_order: 2,
        options: [
          { label: '2 Installments', value: '2' },
          { label: '3 Installments', value: '3' },
          { label: '4 Installments', value: '4' },
        ],
      },
      { id: 6, label: 'Reason', field_name: 'reason', field_type: 'textarea', is_required: true, display_order: 3 },
    ],
  },
  {
    id: 3,
    name: 'Course Drop',
    icon: '📚',
    description: 'Request to drop a registered course.',
    fields: [
      { id: 7, label: 'Course Code', field_name: 'course_code', field_type: 'text', is_required: true, display_order: 1 },
      { id: 8, label: 'Course Name', field_name: 'course_name', field_type: 'text', is_required: true, display_order: 2 },
      { id: 9, label: 'Reason', field_name: 'reason', field_type: 'textarea', is_required: true, display_order: 3 },
    ],
  },
  {
    id: 4,
    name: 'Course Registration',
    icon: '📝',
    description: 'Request course registration or enrollment.',
    fields: [
      { id: 10, label: 'Course Code', field_name: 'course_code', field_type: 'text', is_required: true, display_order: 1 },
      { id: 11, label: 'Course Name', field_name: 'course_name', field_type: 'text', is_required: true, display_order: 2 },
      {
        id: 12,
        label: 'Semester',
        field_name: 'semester',
        field_type: 'dropdown',
        is_required: true,
        display_order: 3,
        options: Array.from({ length: 8 }, (_, i) => ({
          label: `${i + 1}${['st', 'nd', 'rd'][i] || 'th'} Semester`,
          value: String(i + 1),
        })),
      },
    ],
  },
  {
    id: 5,
    name: 'Medical Emergency',
    icon: '🏥',
    description: 'Submit a medical emergency request.',
    fields: [
      { id: 13, label: 'Incident Date', field_name: 'incident_date', field_type: 'date', is_required: true, display_order: 1 },
      { id: 14, label: 'Emergency Details', field_name: 'emergency_details', field_type: 'textarea', is_required: true, display_order: 2 },
      { id: 15, label: 'Hospital / Doctor', field_name: 'hospital_doctor', field_type: 'text', is_required: false, display_order: 3 },
    ],
  },
  {
    id: 6,
    name: 'Scholarship Request',
    icon: '🎓',
    description: 'Request financial or scholarship assistance.',
    fields: [
      { id: 17, label: 'Scholarship Name', field_name: 'scholarship_name', field_type: 'text', is_required: true, display_order: 1 },
      { id: 18, label: 'Current GPA', field_name: 'current_gpa', field_type: 'number', is_required: true, display_order: 2 },
      { id: 19, label: 'Reason', field_name: 'reason', field_type: 'textarea', is_required: true, display_order: 3 },
    ],
  },
]

function getStatusClass(status) {
  const normalized = (status || 'submitted').toLowerCase().replaceAll(' ', '_')
  return `status-chip ${normalized}`
}

function formatStatus(status) {
  return (status || 'submitted')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function Applications() {
  const { user } = useAuth()
  const role = user?.user_type || 'student'
  const currentUser = user?.username || user?.first_name || 'Student'

  const [selected, setSelected] = useState(null)
  const [selectedApplication, setSelectedApplication] = useState(null)
  const [formData, setFormData] = useState({})
  const [commentText, setCommentText] = useState('')
  const [attachmentFile, setAttachmentFile] = useState(null)
  const [notice, setNotice] = useState('')

  const [applications, setApplications] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('ic_applications') || '[]')
      return Array.isArray(saved) ? saved : []
    } catch {
      return []
    }
  })

  function saveApplications(updated) {
    setApplications(updated)
    localStorage.setItem('ic_applications', JSON.stringify(updated))

    if (selectedApplication) {
      const refreshed = updated.find(
        (app) => app.id === selectedApplication.id
      )
      setSelectedApplication(refreshed || null)
    }
  }

  function updateField(fieldName, value) {
    setFormData((previous) => ({
      ...previous,
      [fieldName]: value,
    }))
  }

  function handleSubmit(e) {
    e.preventDefault()

    const trackingNumber = `DEMO-${Date.now().toString().slice(-6)}`
    const submittedAt = new Date().toLocaleString()

    const newApplication = {
      id: trackingNumber,
      trackingNumber,
      type: selected.name,
      applicationTypeId: selected.id,
      date: new Date().toLocaleDateString(),
      status: 'submitted',
      currentStep: 'Application Submitted',
      data: { ...formData },
      comments: [],
      attachments: [],
      approvalHistory: [
        {
          action: 'submitted',
          step: 'Student Submission',
          remarks: 'Application submitted successfully.',
          date: submittedAt,
        },
      ],
    }

    const updated = [newApplication, ...applications]

    setApplications(updated)
    localStorage.setItem('ic_applications', JSON.stringify(updated))

    setSelected(null)
    setFormData({})
    setNotice('Your application has been submitted successfully!')
  }

  function handleBack() {
    setSelected(null)
    setSelectedApplication(null)
    setFormData({})
    setCommentText('')
    setAttachmentFile(null)
  }

  function addComment(e) {
    e.preventDefault()

    if (!commentText.trim() || !selectedApplication) return

    const newComment = {
      id: `COMMENT-${Date.now()}`,
      comment: commentText.trim(),
      user: currentUser,
      createdAt: new Date().toLocaleString(),
    }

    const updated = applications.map((app) =>
      app.id === selectedApplication.id
        ? {
            ...app,
            comments: [...(app.comments || []), newComment],
          }
        : app
    )

    saveApplications(updated)
    setCommentText('')
    setNotice('Comment added successfully!')
  }

  function addAttachment(e) {
    e.preventDefault()

    if (!attachmentFile || !selectedApplication) return

    const newAttachment = {
      id: `FILE-${Date.now()}`,
      fileName: attachmentFile.name,
      fileSize: attachmentFile.size,
      fileType: attachmentFile.type,
      uploadedBy: currentUser,
      uploadedAt: new Date().toLocaleString(),
    }

    const updated = applications.map((app) =>
      app.id === selectedApplication.id
        ? {
            ...app,
            attachments: [...(app.attachments || []), newAttachment],
          }
        : app
    )

    saveApplications(updated)
    setAttachmentFile(null)
    e.target.reset()
    setNotice('Attachment added successfully!')
  }

  function renderField(field) {
    const commonProps = {
      id: field.field_name,
      name: field.field_name,
      required: field.is_required,
      placeholder: field.placeholder || `Enter ${field.label}`,
      value: formData[field.field_name] || '',
      onChange: (e) => updateField(field.field_name, e.target.value),
    }

    switch (field.field_type) {
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
                  onChange={(e) => updateField(field.field_name, e.target.value)}
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
                        : currentValues.filter((value) => value !== option.value)

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
                <span>{selectedApplication.trackingNumber || selectedApplication.id}</span>
              </div>

              <div className="application-list-item">
                <strong>Current Workflow Step</strong>
                <span>{selectedApplication.currentStep || 'Not assigned yet'}</span>
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

              {Object.entries(selectedApplication.data || {}).map(([field, value]) => (
                <div className="application-list-item" key={field}>
                  <strong>{field.replaceAll('_', ' ')}</strong>
                  <span>
                    {Array.isArray(value) ? value.join(', ') : value || 'Not provided'}
                  </span>
                </div>
              ))}
            </div>

            {/* APPLICATION HISTORY */}
            <div className="tracking-history">
              <h3>Application History</h3>

              {(selectedApplication.approvalHistory || []).length === 0 ? (
                <p>No approval history available yet.</p>
              ) : (
                <div className="tracking-timeline">
                  {selectedApplication.approvalHistory.map((item, index) => (
                    <div className="tracking-timeline-item" key={index}>
                      <div className="tracking-timeline-dot" />
                      <div>
                        <strong>{formatStatus(item.action)}</strong>
                        <p>{item.step}</p>
                        <p>{item.remarks}</p>
                        <small>{item.date}</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ATTACHMENTS */}
            <div className="communication-section">
              <h3>Supporting Documents</h3>
              <p className="muted-note">
                Attach documents related to this application.
              </p>

              <form className="attachment-form" onSubmit={addAttachment}>
                <input
                  type="file"
                  onChange={(e) => setAttachmentFile(e.target.files?.[0] || null)}
                  required
                />
                <button type="submit" className="primary-button">
                  Upload Attachment
                </button>
              </form>

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
                        <strong>{file.fileName}</strong>
                        <small>
                          Uploaded by {file.uploadedBy} · {file.uploadedAt}
                        </small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* COMMENTS */}
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
                  disabled={!commentText.trim()}
                >
                  Add Comment
                </button>
              </form>

              {(selectedApplication.comments || []).length === 0 ? (
                <p className="empty-communication">
                  No comments yet.
                </p>
              ) : (
                <div className="comment-list">
                  {selectedApplication.comments.map((comment) => (
                    <div className="comment-item" key={comment.id}>
                      <div className="comment-heading">
                        <strong>{comment.user}</strong>
                        <small>{comment.createdAt}</small>
                      </div>
                      <p>{comment.comment}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <p className="muted-note">
              Demo mode: comments and attachment details are stored in this browser.
              Actual file storage will be connected to the backend later.
            </p>
          </section>
        ) : selected ? (
          <section className="panel application-form-panel">
            <div className="panel-header">
              <div>
                <div className="eyebrow">NEW REQUEST</div>
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
                <button type="button" className="secondary-button" onClick={handleBack}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Submit Application →
                </button>
              </div>
            </form>

            <p className="muted-note">
              Demo mode: your request is saved in this browser.
              Backend submission will be connected later.
            </p>
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
                  <span className="application-type-icon">{item.icon}</span>
                  <h3>{item.name}</h3>
                  <p>{item.description}</p>
                  <span className="application-card-link">
                    Start application →
                  </span>
                </button>
              ))}
            </div>
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

            {applications.length === 0 ? (
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

            <p className="muted-note">
              Demo storage only. Live status updates require backend integration.
            </p>
          </section>
        )}

      </div>
    </DashboardLayout>
  )
}

export default Applications
