import { useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import {
  fetchAllApplications,
  fetchApplicationTracking,
  fetchApplicationAttachments,
  fetchApplicationComments,
} from '../services/applicationService'
import { useAuth } from '../hooks/useAuth'

function formatStatus(status) {
  return (status || 'submitted')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function getStatusClass(status) {
  return `status-chip ${(status || 'submitted').toLowerCase().replaceAll(' ', '_')}`
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

export default function AdminApplications() {
  const { user } = useAuth()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selected, setSelected] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [attachments, setAttachments] = useState([])
  const [comments, setComments] = useState([])

  useEffect(() => {
    let active = true

    async function loadApplications() {
      try {
        setLoading(true)
        setError('')
        const data = await fetchAllApplications()

        if (active) {
          setApplications(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        console.error('Admin applications error:', err)
        if (active) {
          setError(err.response?.data?.detail || 'Unable to load applications.')
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    loadApplications()
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!selected?.id) {
      setHistory([])
      setAttachments([])
      setComments([])
      return
    }

    let active = true

    async function loadHistory() {
      try {
        setLoadingHistory(true)
        const [data, files, notes] = await Promise.all([
          fetchApplicationTracking(selected.id),
          fetchApplicationAttachments(selected.id),
          fetchApplicationComments(selected.id),
        ])
        if (active) {
          setHistory(data.history || [])
          setAttachments(files)
          setComments(notes)
        }
      } catch (err) {
        console.error('Application history error:', err)
        if (active) setHistory([])
        if (active) {
          setAttachments([])
          setComments([])
        }
      } finally {
        if (active) setLoadingHistory(false)
      }
    }

    loadHistory()
    return () => { active = false }
  }, [selected?.id])

  const filteredApplications = useMemo(() => {
    const term = search.trim().toLowerCase()

    return applications.filter((app) => {
      const matchesSearch = !term || [
        app.tracking_number,
        app.student_name,
        app.registration_number,
        app.application_type_name,
        app.title,
      ].some((value) => String(value || '').toLowerCase().includes(term))

      const matchesStatus = statusFilter === 'all' || app.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [applications, search, statusFilter])

  if (user?.user_type !== 'admin') {
    return (
      <DashboardLayout role={user?.user_type || 'student'}>
        <div className="application-page">
          <div className="application-notice">You are not authorized to access this page.</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout role="admin">
      <div className="application-page">
        <div className="page-heading">
          <div>
            <div className="eyebrow">ADMINISTRATION</div>
            <h1>All Applications</h1>
            <p>Monitor university applications submitted by students.</p>
          </div>
          <span className="application-count">{applications.length} Total</span>
        </div>

        {error && <div className="application-notice">{error}</div>}

        {!selected ? (
          <section className="panel my-applications-panel">
            <div className="panel-header">
              <div>
                <h2>Application Records</h2>
                <p>Search, filter and inspect submitted applications.</p>
              </div>
            </div>

            <div className="filter-row">
              <input
                className="search-box"
                type="search"
                placeholder="Search tracking number, student or type..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">All statuses</option>
                {[...new Set(applications.map((app) => app.status).filter(Boolean))].map((status) => (
                  <option key={status} value={status}>{formatStatus(status)}</option>
                ))}
              </select>
            </div>

            {loading ? (
              <p>Loading applications...</p>
            ) : filteredApplications.length === 0 ? (
              <div className="empty-state">
                <h3>No applications found</h3>
                <p>Try changing your search or status filter.</p>
              </div>
            ) : (
              <div className="application-list">
                {filteredApplications.map((app) => (
                  <div className="application-list-item" key={app.id}>
                    <div>
                      <strong>{app.application_type_name || app.title || 'Application'}</strong>
                      <small>
                        {app.tracking_number} · {app.student_name || 'Student'} · {app.registration_number || 'No registration number'}
                      </small>
                      <small>Submitted: {formatDate(app.submitted_at)}</small>
                    </div>
                    <div>
                      <span className={getStatusClass(app.status)}>{formatStatus(app.status)}</span>
                      <button className="secondary-button" onClick={() => setSelected(app)}>
                        View Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        ) : (
          <section className="panel application-form-panel">
            <div className="panel-header">
              <div>
                <div className="eyebrow">APPLICATION DETAILS</div>
                <h2>{selected.application_type_name || selected.title}</h2>
                <p>{selected.tracking_number}</p>
              </div>
              <button className="secondary-button" onClick={() => setSelected(null)}>
                Back to Applications
              </button>
            </div>

            <div className="application-list">
              {[
                ['Student', selected.student_name],
                ['Registration Number', selected.registration_number],
                ['Application Title', selected.title],
                ['Application Type', selected.application_type_name],
                ['Priority', selected.priority],
                ['Workflow', selected.workflow_name],
                ['Current Step', selected.current_step_name || 'Not assigned yet'],
                ['Status', formatStatus(selected.status)],
                ['Submitted At', formatDate(selected.submitted_at)],
                ['Completed At', formatDate(selected.completed_at)],
                ['Description', selected.description],
              ].map(([label, value]) => (
                <div className="application-list-item" key={label}>
                  <strong>{label}</strong>
                  <span>{value || '—'}</span>
                </div>
              ))}

              {Object.entries(selected.form_data || {}).map(([field, value]) => (
                <div className="application-list-item" key={field}>
                  <strong>{field.replaceAll('_', ' ')}</strong>
                  <span>{Array.isArray(value) ? value.join(', ') : String(value ?? '—')}</span>
                </div>
              ))}
            </div>

            <div className="tracking-history">
              <h3>Approval History</h3>
              {loadingHistory ? (
                <p>Loading history...</p>
              ) : history.length === 0 ? (
                <p>No approval history available.</p>
              ) : (
                <div className="history-list">
                  {history.map((item) => (
                    <div className="history-item" key={item.id}>
                      <strong>{formatStatus(item.action)}</strong>
                      <p><strong>Step:</strong> {item.step}</p>
                      <p><strong>Officer:</strong> {item.action_by}{item.designation ? ` (${item.designation})` : ''}</p>
                      {item.remarks && <p><strong>Remarks:</strong> {item.remarks}</p>}
                      <small>{formatDate(item.action_date)}</small>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <section className="communication-section">
              <h3>Supporting Documents</h3>
              {attachments.length === 0 ? <p>No documents attached.</p> : attachments.map((file) => (
                <div className="attachment-item" key={file.id}>
                  <a href={file.file_path} target="_blank" rel="noreferrer">{file.file_name}</a>
                  <small>Uploaded by {file.uploaded_by_name || 'User'} · {formatDate(file.uploaded_at)}</small>
                </div>
              ))}
            </section>

            <section className="communication-section">
              <h3>Comments</h3>
              {comments.length === 0 ? <p>No comments on this application.</p> : comments.map((comment) => (
                <div className="comment-item" key={comment.id}>
                  <div className="comment-heading"><strong>{comment.user_name || 'User'}</strong><small>{formatDate(comment.created_at)}</small></div>
                  <p>{comment.comment}</p>
                </div>
              ))}
            </section>
          </section>
        )}
      </div>
    </DashboardLayout>
  )
}
