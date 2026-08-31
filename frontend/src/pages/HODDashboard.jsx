import DashboardLayout from '../components/DashboardLayout'

function HODDashboard() {
  const email = localStorage.getItem('userEmail')

  return (
    <DashboardLayout role="hod">
      <div className="dashboard-welcome">
        <h1>HOD Dashboard</h1>

        <p>
          Welcome back, {email || 'HOD'}!
        </p>
      </div>

      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>Department Overview</h3>
          <p>View your department information.</p>
        </div>

        <div className="dashboard-card">
          <h3>Student Management</h3>
          <p>Manage department students.</p>
        </div>

        <div className="dashboard-card">
          <h3>Teacher Management</h3>
          <p>Manage faculty members.</p>
        </div>

        <div className="dashboard-card">
          <h3>Applications</h3>
          <p>Review important applications.</p>
        </div>

        <div className="dashboard-card">
          <h3>Reports</h3>
          <p>View department reports.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default HODDashboard