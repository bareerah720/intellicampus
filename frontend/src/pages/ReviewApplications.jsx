
import { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import {
  fetchOfficerInbox,
  reviewApplication,
  fetchApplicationTracking,
  fetchApplicationAttachments,
  fetchApplicationComments,
  createApplicationComment,
} from '../services/applicationService'

function formatStatus(status) {
  return (status || 'submitted')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function getStatusClass(status) {
  return `status-chip ${(status || 'submitted').toLowerCase()}`
}

function ReviewApplications() {
  const { user } = useAuth()
  const role = user?.user_type || 'student'

  const [applications, setApplications] = useState([])
  const [selected, setSelected] = useState(null)
  const [remarks, setRemarks] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [details, setDetails] = useState(null)
  const [commentText, setCommentText] = useState('')
  const [savingComment, setSavingComment] = useState(false)

  async function loadInbox() {
    try {
      setLoading(true)
      const data = await fetchOfficerInbox()
      setApplications(Array.isArray(data) ? data : [])
    } catch (error) {
      setNotice(
        error.response?.data?.detail ||
        'Unable to load applications. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInbox()
  }, [])

  useEffect(() => {
    if (!selected?.id) {
      setDetails(null)
      return undefined
    }

    let active = true
    Promise.all([
      fetchApplicationTracking(selected.id),
      fetchApplicationAttachments(selected.id),
      fetchApplicationComments(selected.id),
    ]).then(([tracking, attachments, comments]) => {
      if (active) setDetails({ tracking, attachments, comments })
    }).catch((error) => {
      if (active) {
        setDetails(null)
        setNotice(error.response?.data?.detail || 'Unable to load application details.')
      }
    })

    return () => { active = false }
  }, [selected?.id])

  async function handleAction(action) {
    if (!selected || submitting) return

    if (action !== 'approved' && !remarks.trim()) {
      setNotice('Please enter remarks before continuing.')
      return
    }

    try {
      setSubmitting(true)

      const result = await reviewApplication(
        selected.id,
        action,
        remarks.trim()
      )

      setNotice(result.message || 'Application updated successfully.')
      setSelected(null)
      setRemarks('')

      await loadInbox()
    } catch (error) {
      setNotice(
        error.response?.data?.detail ||
        'Action failed. Please try again.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleAddComment(event) {
    event.preventDefault()
    if (!commentText.trim() || !selected) return
    try {
      setSavingComment(true)
      const created = await createApplicationComment(selected.id, commentText.trim())
      setDetails((current) => current
        ? { ...current, comments: [...current.comments, created] }
        : current)
      setCommentText('')
      setNotice('Comment added.')
    } catch (error) {
      setNotice(error.response?.data?.detail || 'Could not add comment.')
    } finally {
      setSavingComment(false)
    }
  }

  if (!['admin', 'faculty', 'staff'].includes(role)) {
    return (
      <DashboardLayout role={role}>
        <div className="application-page">
          <section className="panel empty-state">
            <h2>Access Restricted</h2>
            <p>You do not have permission to review applications.</p>
          </section>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout role={role}>
      <div className="application-page">
        <div className="page-heading">
          <div>
            <div className="eyebrow">APPLICATION MANAGEMENT</div>
            <h1>Review Applications</h1>
            <p>Review applications assigned to your responsibility.</p>
          </div>
        </div>

        {notice && (
          <div className="application-notice">
            {notice}
            <button onClick={() => setNotice('')}>×</button>
          </div>
        )}

        {loading ? (
          <section className="panel empty-state">
            <p>Loading applications...</p>
          </section>
        ) : selected ? (
          <section className="panel application-form-panel">
            <div className="panel-header">
              <div>
                <div className="eyebrow">APPLICATION REVIEW</div>
                <h2>{selected.application_type_name || selected.title}</h2>
                <p>Tracking Number: {selected.tracking_number}</p>
              </div>

              <button
                className="secondary-button"
                onClick={() => {
                  setSelected(null)
                  setRemarks('')
                }}
              >
                Back
              </button>
            </div>

            <div className="application-list">
              <div className="application-list-item">
                <strong>Student Name</strong>
                <span>{selected.student_name || 'Not available'}</span>
              </div>

              <div className="application-list-item">
                <strong>Registration Number</strong>
                <span>{selected.registration_number || 'Not available'}</span>
              </div>

              <div className="application-list-item">
                <strong>Submission Date</strong>
                <span>
                  {selected.submitted_at
                    ? new Date(selected.submitted_at).toLocaleString()
                    : 'Not available'}
                </span>
              </div>

              <div className="application-list-item">
                <strong>Status</strong>
                <span className={getStatusClass(selected.status)}>
                  {formatStatus(selected.status)}
                </span>
              </div>

              <div className="application-list-item">
                <strong>Current Workflow Step</strong>
                <span>{selected.current_step_name || 'Not assigned'}</span>
              </div>

              <div className="application-list-item">
                <strong>Title</strong>
                <span>{selected.title || 'Not provided'}</span>
              </div>

              <div className="application-list-item">
                <strong>Description</strong>
                <span>{selected.description || 'Not provided'}</span>
              </div>

              {Object.entries(selected.form_data || {}).map(([field, value]) => (
                <div className="application-list-item" key={field}>
                  <strong>{field.replaceAll('_', ' ')}</strong>
                  <span>
                    {Array.isArray(value)
                      ? value.join(', ')
                      : String(value ?? 'Not provided')}
                  </span>
                </div>
              ))}
            </div>

            {details?.tracking?.current_officer && (
              <section className="communication-section">
                <h3>Responsible Officer</h3>
                <p>
                  {details.tracking.current_officer.name}
                  {details.tracking.current_officer.designation ? ` · ${details.tracking.current_officer.designation}` : ''}
                  {details.tracking.current_officer.email ? ` · ${details.tracking.current_officer.email}` : ''}
                  {details.tracking.current_officer.office_email ? ` · ${details.tracking.current_officer.office_email}` : ''}
                  {details.tracking.current_officer.office_contact_number ? ` · ${details.tracking.current_officer.office_contact_number}` : ''}
                </p>
              </section>
            )}

            <section className="communication-section">
              <h3>Supporting Documents</h3>
              {!details ? <p>Loading documents...</p> : details.attachments.length === 0 ? (
                <p className="empty-communication">No documents attached.</p>
              ) : (
                <div className="attachment-list">
                  {details.attachments.map((file) => (
                    <div className="attachment-item" key={file.id}>
                      <a href={file.file_path} target="_blank" rel="noreferrer">{file.file_name}</a>
                      <small>Uploaded by {file.uploaded_by_name || 'User'} · {new Date(file.uploaded_at).toLocaleString()}</small>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="communication-section">
              <h3>Application Comments</h3>
              <form className="comment-form" onSubmit={handleAddComment}>
                <textarea rows={3} value={commentText} onChange={(event) => setCommentText(event.target.value)} placeholder="Add a note to this application" required />
                <button className="primary-button" type="submit" disabled={!commentText.trim() || savingComment}>
                  {savingComment ? 'Saving...' : 'Add Comment'}
                </button>
              </form>
              {!details ? <p>Loading comments...</p> : details.comments.length === 0 ? (
                <p className="empty-communication">No comments yet.</p>
              ) : (
                <div className="comment-list">
                  {details.comments.map((comment) => (
                    <div className="comment-item" key={comment.id}>
                      <div className="comment-heading"><strong>{comment.user_name || 'User'}</strong><small>{new Date(comment.created_at).toLocaleString()}</small></div>
                      <p>{comment.comment}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="tracking-history">
              <h3>Approval History</h3>
              {!details ? <p>Loading history...</p> : details.tracking.history.length === 0 ? (
                <p>No approval history yet.</p>
              ) : details.tracking.history.map((entry) => (
                <div className="history-item" key={entry.id}>
                  <strong>{formatStatus(entry.action)}</strong>
                  <p>{entry.step} · {entry.action_by}{entry.designation ? ` (${entry.designation})` : ''}</p>
                  {entry.remarks && <p>{entry.remarks}</p>}
                  <small>{new Date(entry.action_date).toLocaleString()}</small>
                </div>
              ))}
            </section>

            <div className="review-action-panel">
              <h3>Review Decision</h3>

              <label>
                Remarks
                <textarea
                  rows={4}
                  placeholder="Enter remarks, rejection reason or revision instructions..."
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                />
              </label>

              <div className="application-form-actions">
                <button
                  className="primary-button"
                  disabled={submitting}
                  onClick={() => handleAction('approved')}
                >
                  {submitting ? 'Processing...' : 'Approve / Forward'}
                </button>

                <button
                  className="secondary-button"
                  disabled={submitting || !remarks.trim()}
                  onClick={() => handleAction('revision_required')}
                >
                  Request Revision
                </button>

                <button
                  className="secondary-button"
                  disabled={submitting || !remarks.trim()}
                  onClick={() => handleAction('rejected')}
                >
                  Reject Application
                </button>
              </div>
            </div>
          </section>
        ) : (
          <>
            <div className="application-section-heading">
              <div>
                <h2>Applications Awaiting Review</h2>
                <p>Applications currently assigned to you.</p>
              </div>
              <span>{applications.length} Pending</span>
            </div>

            <section className="panel my-applications-panel">
              {applications.length === 0 ? (
                <div className="empty-state">
                  <h3>No pending applications</h3>
                  <p>Applications assigned to you will appear here.</p>
                </div>
              ) : (
                <div className="application-list">
                  {applications.map((app) => (
                    <div className="application-list-item" key={app.id}>
                      <div>
                        <strong>
                          {app.application_type_name || app.title}
                        </strong>
                        <small>
                          Tracking: {app.tracking_number}
                          {' · '}
                          {app.student_name || 'Student'}
                        </small>
                      </div>

                      <div>
                        <span className={getStatusClass(app.status)}>
                          {formatStatus(app.status)}
                        </span>

                        <button
                          className="secondary-button"
                          onClick={() => {
                            setSelected(app)
                            setRemarks('')
                          }}
                        >
                          Review Details →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}

export default ReviewApplications
