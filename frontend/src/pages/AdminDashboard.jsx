import DashboardLayout from '../components/DashboardLayout'

function AdminDashboard() {
  const email = localStorage.getItem('userEmail')

  return (
    <DashboardLayout role="admin">
      <div className="dashboard-welcome">
        <h1>Admin Dashboard</h1>

        <p>
          Welcome back, {email || 'Administrator'}!
        </p>
      </div>

      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>User Management</h3>
          <p>Manage system users.</p>
        </div>

        <div className="dashboard-card">
          <h3>Role Management</h3>
          <p>Manage user roles and permissions.</p>
        </div>

        <div className="dashboard-card">
          <h3>System Management</h3>
          <p>Manage system settings.</p>
        </div>

        <div className="dashboard-card">
          <h3>Reports</h3>
          <p>View system reports.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default AdminDashboard