import DashboardLayout from '../components/DashboardLayout'

function TeacherDashboard() {
  const email = localStorage.getItem('userEmail')

  return (
    <DashboardLayout role="teacher">
      <div className="dashboard-welcome">
        <h1>Teacher Dashboard</h1>

        <p>
          Welcome back, {email || 'Teacher'}!
        </p>
      </div>

      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>My Profile</h3>
          <p>View and manage your profile.</p>
        </div>

        <div className="dashboard-card">
          <h3>Student Applications</h3>
          <p>Review student applications.</p>
        </div>

        <div className="dashboard-card">
          <h3>Internship Requests</h3>
          <p>Manage internship-related requests.</p>
        </div>

        <div className="dashboard-card">
          <h3>FYP Supervision</h3>
          <p>Manage your supervised projects.</p>
        </div>

        <div className="dashboard-card">
          <h3>Announcements</h3>
          <p>View important announcements.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default TeacherDashboard