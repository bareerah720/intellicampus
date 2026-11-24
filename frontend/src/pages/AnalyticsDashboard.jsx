import { useEffect, useMemo, useState } from 'react'
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Bar, Doughnut, Line } from 'react-chartjs-2'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import { fetchAnalytics } from '../services/analyticsService'

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
)

const statusLabels = {
  submitted: 'Submitted',
  in_progress: 'In Progress',
  approved: 'Approved',
  rejected: 'Rejected',
  revision_required: 'Revision Required',
}

function EmptyChart({ text = 'No data available.' }) {
  return <p className="empty-state">{text}</p>
}

export default function AnalyticsDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadAnalytics() {
    setLoading(true)
    setError('')
    try {
      setData(await fetchAnalytics())
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
        'Unable to load analytics.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user?.user_type === 'admin') loadAnalytics()
  }, [user?.user_type])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' },
    },
  }), [])

  if (user?.user_type !== 'admin') {
    return (
      <DashboardLayout role={user?.user_type || 'student'}>
        <div className="application-notice">Only administrators can view analytics.</div>
      </DashboardLayout>
    )
  }

  const departmentData = data?.department_distribution || []
  const semesterData = data?.semester_distribution || []
  const statusData = data?.application_status || {}
  const typeData = data?.application_types || []
  const submissions = data?.monthly_submissions || []
  const completions = data?.monthly_completions || []
  const forecast = data?.forecast

  const activityMonths = useMemo(() => {
    const observedMonths = [...submissions, ...completions]
      .map((item) => item.month)
      .sort()
    if (!observedMonths.length) return []

    const monthIndex = (month) => {
      const [year, monthNumber] = month.split('-').map(Number)
      return year * 12 + monthNumber - 1
    }
    const first = monthIndex(observedMonths[0])
    const last = monthIndex(observedMonths[observedMonths.length - 1])

    return Array.from({ length: last - first + 1 }, (_, index) => {
      const current = first + index
      return `${Math.floor(current / 12)}-${String(current % 12 + 1).padStart(2, '0')}`
    })
  }, [submissions, completions])

  const statusChartData = {
    labels: Object.keys(statusData).map((key) => statusLabels[key] || key),
    datasets: [{
      data: Object.values(statusData),
      backgroundColor: ['#74a6a0', '#6679a8', '#3b8f72', '#d66a6a', '#d8a94c'],
    }],
  }

  const departmentChartData = {
    labels: departmentData.map((item) => item.department),
    datasets: [{
      label: 'Students',
      data: departmentData.map((item) => item.count),
      backgroundColor: '#4f8b84',
    }],
  }

  const semesterChartData = {
    labels: semesterData.map((item) => item.semester),
    datasets: [{
      label: 'Students',
      data: semesterData.map((item) => item.count),
      backgroundColor: '#6679a8',
    }],
  }

  const typeChartData = {
    labels: typeData.map((item) => item.application_type),
    datasets: [{
      label: 'Applications',
      data: typeData.map((item) => item.count),
      backgroundColor: '#d8a94c',
    }],
  }

  const submissionCompletionChartData = {
    labels: activityMonths,
    datasets: [
      {
        label: 'Submitted',
        data: activityMonths.map((month) =>
          submissions.find((item) => item.month === month)?.count || 0
        ),
        borderColor: '#4f8b84',
        backgroundColor: 'rgba(79,139,132,.15)',
      },
      {
        label: 'Completed',
        data: activityMonths.map((month) =>
          completions.find((item) => item.month === month)?.count || 0
        ),
        borderColor: '#6679a8',
        backgroundColor: 'rgba(102,121,168,.15)',
      },
    ],
  }

  const forecastChartData = forecast?.available ? {
    labels: [
      ...forecast.actual.map((item) => item.month),
      ...forecast.predicted.map((item) => item.month),
    ],
    datasets: [
      {
        label: 'Actual',
        data: [
          ...forecast.actual.map((item) => item.count),
          ...forecast.predicted.map(() => null),
        ],
        borderColor: '#4f8b84',
        backgroundColor: 'rgba(79,139,132,.15)',
        spanGaps: true,
      },
      {
        label: 'Forecast',
        data: [
          ...forecast.actual.map((item, index) =>
            index === forecast.actual.length - 1 ? item.count : null
          ),
          ...forecast.predicted.map((item) => item.count),
        ],
        borderColor: '#d8a94c',
        borderDash: [6, 4],
        backgroundColor: 'rgba(216,169,76,.15)',
        spanGaps: true,
      },
    ],
  } : null

  return (
    <DashboardLayout role="admin">
      <div className="application-page">
        <div className="page-heading">
          <div>
            <div className="eyebrow">ADMINISTRATION</div>
            <h1>Analytics Dashboard</h1>
            <p>Real-time university population and application insights.</p>
          </div>
        </div>

        {error && (
          <div className="application-notice" role="alert">
            {error}
            <button onClick={loadAnalytics}>Retry</button>
          </div>
        )}

        {loading ? (
          <section className="panel"><p>Loading analytics…</p></section>
        ) : data ? (
          <>
            <div className="metric-grid three">
              {[
                ['Total students', data.totals.students],
                ['Faculty', data.totals.faculty],
                ['Staff', data.totals.staff],
                ['Total applications', data.totals.applications],
                ['Approved', data.application_status.approved],
                ['Rejected', data.application_status.rejected],
              ].map(([label, value]) => (
                <div className="metric-card" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>Live database record</small>
                </div>
              ))}
            </div>

            <div className="two-column">
              <section className="panel">
                <div className="panel-header"><div><h2>Students by department</h2></div></div>
                <div style={{ height: 300 }}>
                  {departmentData.length
                    ? <Bar data={departmentChartData} options={chartOptions} />
                    : <EmptyChart />}
                </div>
              </section>
              <section className="panel">
                <div className="panel-header"><div><h2>Students by semester</h2></div></div>
                <div style={{ height: 300 }}>
                  {semesterData.length
                    ? <Bar data={semesterChartData} options={chartOptions} />
                    : <EmptyChart />}
                </div>
              </section>
            </div>

            <div className="two-column">
              <section className="panel">
                <div className="panel-header"><div><h2>Application status</h2></div></div>
                <div style={{ height: 300 }}>
                  {Object.values(statusData).some((count) => count > 0)
                    ? <Doughnut data={statusChartData} options={chartOptions} />
                    : <EmptyChart />}
                </div>
              </section>
              <section className="panel">
                <div className="panel-header"><div><h2>Applications by type</h2></div></div>
                <div style={{ height: 300 }}>
                  {typeData.length
                    ? <Bar data={typeChartData} options={chartOptions} />
                    : <EmptyChart />}
                </div>
              </section>
            </div>

            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Monthly application activity</h2>
                  <p>Submission and completion records using actual timestamps.</p>
                </div>
              </div>
              <div style={{ height: 340 }}>
                {submissions.length || completions.length
                  ? <Line data={submissionCompletionChartData} options={chartOptions} />
                  : <EmptyChart text="No monthly application history is available." />}
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Submission forecast</h2>
                  <p>{forecast?.period}</p>
                </div>
              </div>
              {forecast?.available ? (
                <>
                  <p className="muted-note">{forecast.disclaimer}</p>
                  <div style={{ height: 340 }}>
                    <Line data={forecastChartData} options={chartOptions} />
                  </div>
                </>
              ) : (
                <p className="empty-state">
                  {forecast?.message || 'More historical monthly application data is required.'}
                </p>
              )}
            </section>
          </>
        ) : null}
      </div>
    </DashboardLayout>
  )
}
