
import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'

function formatStatus(status) {
  return (status || 'submitted')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function getStatusClass(status) {
  const normalized = (status || 'submitted').toLowerCase().replaceAll(' ', '_')
  return `status-chip ${normalized}`
}

function ReviewApplications() {
  const { user } = useAuth()
  const role = user?.user_type || 'student'
  const currentUser = user?.username || user?.first_name || role

  const [applications, setApplications] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem('ic_applications') || '[]'
      )
      return Array.isArray(saved) ? saved : []
    } catch {
      return []
    }
  })

  const [selected, setSelected] = useState(null)
  const [remarks, setRemarks] = useState('')
  const [commentText, setCommentText] = useState('')
  const [notice, setNotice] = useState('')

  const reviewers = ['admin', 'faculty', 'staff']

  const pendingApplications = applications.filter((app) =>
    ['submitted', 'in_progress', 'revision_required'].includes(
      (app.status || '').toLowerCase()
    )
  )

  function handleBack() {
    setSelected(null)
    setRemarks('')
    setCommentText('')
  }

  function addReviewerComment(e) {
    e.preventDefault()

    if (!selected || !commentText.trim()) return

    const newComment = {
      id: `COMMENT-${Date.now()}`,
      comment: commentText.trim(),
      user: currentUser,
      createdAt: new Date().toLocaleString(),
    }

    const updated = applications.map((app) =>
      app.id === selected.id
        ? {
            ...app,
            comments: [...(app.comments || []), newComment],
          }
        : app
    )

    setApplications(updated)
    localStorage.setItem('ic_applications', JSON.stringify(updated))

    const refreshed = updated.find((app) => app.id === selected.id)
    setSelected(refreshed)
    setCommentText('')
    setNotice('Your comment has been added successfully.')
  }

  function updateApplication(action) {
    if (!selected) return

    if (action !== 'approved' && !remarks.trim()) {
      setNotice('Please enter remarks before continuing.')
      return
    }

    const now = new Date().toLocaleString()

    let newStatus = selected.status
    let newStep = selected.currentStep

    if (action === 'approved') {
      // Demo progression only. Backend will determine the actual next step.
      newStatus = 'in_progress'
      newStep = 'Forwarded to next workflow step'
    } else if (action === 'rejected') {
      newStatus = 'rejected'
      newStep = 'Application Rejected'
    } else if (action === 'revision_required') {
      newStatus = 'revision_required'
      newStep = 'Revision Requested'
    }

    const historyEntry = {
      action,
      step: selected.currentStep || 'Application Review',
      remarks: remarks.trim() || 'Application approved and forwarded.',
      date: now,
      reviewer: currentUser,
    }

    const updated = applications.map((app) =>
      app.id === selected.id
        ? {
            ...app,
            status: newStatus,
            currentStep: newStep,
            reviewComment: remarks.trim(),
            reviewedBy: currentUser,
            reviewedAt: now,
            approvalHistory: [
              ...(app.approvalHistory || []),
              historyEntry,
            ],
          }
        : app
    )

    setApplications(updated)
    localStorage.setItem('ic_applications', JSON.stringify(updated))

    setSelected(null)
    setRemarks('')
    setCommentText('')

    const messages = {
      approved: 'Application approved and forwarded in demo mode.',
      rejected: 'Application rejected successfully.',
      revision_required: 'Revision requested successfully.',
    }

    setNotice(messages[action])
  }

  if (!reviewers.includes(role)) {
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
            <p>Review and manage university requests.</p>
          </div>
        </div>

        {notice && (
          <div className="application-notice">
            ✓ {notice}
            <button onClick={() => setNotice('')}>×</button>
          </div>
        )}

        {selected ? (
          <section className="panel application-form-panel">

            <div className="panel-header">
              <div>
                <div className="eyebrow">APPLICATION REVIEW</div>
                <h2>{selected.type}</h2>
                <p>
                  Tracking Number: {selected.trackingNumber || selected.id}
                </p>
              </div>

              <button className="secondary-button" onClick={handleBack}>
                ← Back
              </button>
            </div>

            {/* APPLICATION DETAILS */}
            <div className="application-list">

              <div className="application-list-item">
                <strong>Submission Date</strong>
                <span>{selected.date}</span>
              </div>

              <div className="application-list-item">
                <strong>Current Status</strong>
                <span className={getStatusClass(selected.status)}>
                  {formatStatus(selected.status)}
                </span>
              </div>

              <div className="application-list-item">
                <strong>Current Workflow Step</strong>
                <span>{selected.currentStep || 'Not assigned yet'}</span>
              </div>

              {Object.entries(selected.data || {}).map(([field, value]) => (
                <div className="application-list-item" key={field}>
                  <strong>{field.replaceAll('_', ' ')}</strong>
                  <span>
                    {Array.isArray(value)
                      ? value.join(', ')
                      : value || 'Not provided'}
                  </span>
                </div>
              ))}

            </div>

            {/* ATTACHMENTS */}
            <div className="communication-section">
              <h3>Supporting Documents</h3>
              <p className="muted-note">
                Documents attached by the student.
              </p>

              {(selected.attachments || []).length === 0 ? (
                <p className="empty-communication">
                  No documents attached to this application.
                </p>
              ) : (
                <div className="attachment-list">
                  {selected.attachments.map((file) => (
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
                View student comments and add your own review comments.
              </p>

              {(selected.comments || []).length === 0 ? (
                <p className="empty-communication">
                  No comments available yet.
                </p>
              ) : (
                <div className="comment-list">
                  {selected.comments.map((comment) => (
                    <div className="comment-item" key={comment.id}>
                      <div className="comment-heading">
                        <strong>{comment.user || 'User'}</strong>
                        <small>{comment.createdAt || 'Date unavailable'}</small>
                      </div>
                      <p>{comment.comment}</p>
                    </div>
                  ))}
                </div>
              )}

              <form className="comment-form" onSubmit={addReviewerComment}>
                <textarea
                  rows={3}
                  placeholder="Write a comment for this application..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  required
                />

                <button
                  type="submit"
                  className="primary-button"
                  disabled={!commentText.trim()}
                >
                  Add Reviewer Comment
                </button>
              </form>
            </div>

            {/* APPROVAL HISTORY */}
            <div className="tracking-history">
              <h3>Approval History</h3>

              {(selected.approvalHistory || []).length === 0 ? (
                <p>No approval history available yet.</p>
              ) : (
                <div className="tracking-timeline">
                  {selected.approvalHistory.map((item, index) => (
                    <div className="tracking-timeline-item" key={index}>
                      <div className="tracking-timeline-dot" />
                      <div>
                        <strong>{formatStatus(item.action)}</strong>
                        <p>{item.step}</p>
                        <p>{item.remarks}</p>
                        {item.reviewer && (
                          <p>Reviewer: {item.reviewer}</p>
                        )}
                        <small>{item.date}</small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* REVIEW ACTIONS */}
            {['submitted', 'in_progress', 'revision_required'].includes(
              (selected.status || '').toLowerCase()
            ) ? (
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
                    onClick={() => updateApplication('approved')}
                  >
                    ✓ Approve / Forward
                  </button>

                  <button
                    className="secondary-button"
                    disabled={!remarks.trim()}
                    onClick={() => updateApplication('revision_required')}
                  >
                    Request Revision
                  </button>

                  <button
                    className="secondary-button"
                    disabled={!remarks.trim()}
                    onClick={() => updateApplication('rejected')}
                  >
                    Reject Application
                  </button>

                </div>
              </div>
            ) : (
              <div className="application-notice">
                This application has been finalized.
                <p>Status: {formatStatus(selected.status)}</p>
                {selected.reviewComment && (
                  <p>Remarks: {selected.reviewComment}</p>
                )}
              </div>
            )}

          </section>
        ) : (
          <>
            <div className="application-section-heading">
              <div>
                <h2>Applications Awaiting Review</h2>
                <p>
                  Applications that are submitted or currently in workflow.
                </p>
              </div>

              <span>{pendingApplications.length} Pending</span>
            </div>

            <section className="panel my-applications-panel">

              {pendingApplications.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">▤</div>
                  <h3>No pending applications</h3>
                  <p>Applications waiting for review will appear here.</p>
                </div>
              ) : (
                <div className="application-list">
                  {pendingApplications.map((app) => (
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
                          onClick={() => {
                            setSelected(app)
                            setRemarks('')
                            setCommentText('')
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

        <p className="muted-note">
          Demo mode: review decisions and comments are saved in this browser.
          Real workflow progression, file access and reviewer authorization
          will be handled by the backend.
        </p>

      </div>
    </DashboardLayout>
  )
}

export default ReviewApplications
