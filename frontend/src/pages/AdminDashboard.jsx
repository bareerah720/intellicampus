import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import { fetchAllApplications } from '../services/applicationService'

const statusLabel = (value) => (value || '').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

function countBy(items, key) {
  const counts = new Map()
  items.forEach((item) => {
    const label = item[key] || 'Unassigned'
    counts.set(label, (counts.get(label) || 0) + 1)
  })
  return [...counts.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
}

export default function AdminDashboard() {
  const { user } = useAuth()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadDashboard() {
    try {
      setLoading(true)
      setError('')
      const data = await fetchAllApplications()
      setApplications(Array.isArray(data) ? data : data?.results || [])
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to load application dashboard data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadDashboard() }, [])

  const pending = applications.filter((app) => ['submitted', 'in_progress'].includes(app.status))
  const approved = applications.filter((app) => app.status === 'approved')
  const rejected = applications.filter((app) => app.status === 'rejected')
  const revisionRequested = applications.filter((app) => app.status === 'revision_required')
  const typeBreakdown = useMemo(() => countBy(applications, 'application_type_name'), [applications])
  const departmentBreakdown = useMemo(() => countBy(applications, 'department_name'), [applications])
  const recent = [...applications]
    .sort((a, b) => new Date(b.created_at || b.submitted_at || 0) - new Date(a.created_at || a.submitted_at || 0))
    .slice(0, 8)

  if (user?.user_type !== 'admin') {
    return <DashboardLayout role={user?.user_type || 'student'}><div className="application-notice">You are not authorized to view the admin dashboard.</div></DashboardLayout>
  }

  const metrics = [
    ['Total applications', applications.length],
    ['Pending applications', pending.length],
    ['Approved applications', approved.length],
    ['Rejected applications', rejected.length],
    ['Revision requested', revisionRequested.length],
  ]

  return (
    <DashboardLayout role="admin">
      <div className="application-page">
        <div className="page-heading">
          <div>
            <div className="eyebrow">ADMINISTRATION</div>
            <h1>Application Dashboard</h1>
            <p>Current application activity from the university workflow.</p>
          </div>
          <Link className="primary-button" to="/admin-applications">Monitor all applications →</Link>
        </div>

        {error && <div className="application-notice" role="alert">{error} <button onClick={loadDashboard}>Retry</button></div>}

        <div className="metric-grid three">
          {metrics.map(([label, value]) => (
            <div className="metric-card" key={label}>
              <span>{label}</span>
              <strong>{loading ? '…' : value}</strong>
              <small>Live application records</small>
            </div>
          ))}
        </div>

        <div className="two-column">
          <section className="panel">
            <div className="panel-header"><div><h2>Application types</h2><p>Distribution by configured request type.</p></div></div>
            {loading ? <p>Loading…</p> : typeBreakdown.length === 0 ? <p className="empty-state">No applications yet.</p> : (
              <div className="resource-list">
                {typeBreakdown.map(({ label, count }) => <div className="resource-row" key={label}><strong>{label}</strong><span className="application-count">{count}</span></div>)}
              </div>
            )}
          </section>
          <section className="panel">
            <div className="panel-header"><div><h2>Departments</h2><p>Application volume by student program department.</p></div></div>
            {loading ? <p>Loading…</p> : departmentBreakdown.length === 0 ? <p className="empty-state">No applications yet.</p> : (
              <div className="resource-list">
                {departmentBreakdown.map(({ label, count }) => <div className="resource-row" key={label}><strong>{label}</strong><span className="application-count">{count}</span></div>)}
              </div>
            )}
          </section>
        </div>

        <section className="panel">
          <div className="panel-header">
            <div><h2>Recent applications</h2><p>Latest submissions and status changes.</p></div>
            <Link className="text-link" to="/admin-applications">Open application monitor →</Link>
          </div>
          {loading ? <p>Loading recent applications…</p> : recent.length === 0 ? <p className="empty-state">No applications have been submitted.</p> : (
            <div className="application-list">
              {recent.map((app) => (
                <div className="application-list-item" key={app.id}>
                  <div>
                    <strong>{app.application_type_name || app.title}</strong>
                    <small>{app.tracking_number} · {app.student_name || 'Student'} · {app.department_name || 'Department unassigned'}</small>
                    <small>{new Date(app.submitted_at || app.created_at).toLocaleString()}</small>
                  </div>
                  <span className={`status-chip ${(app.status || '').replaceAll('_', '-')}`}>{statusLabel(app.status)}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  )
}
