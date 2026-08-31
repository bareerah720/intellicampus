import DashboardLayout from '../components/DashboardLayout'

function StudentDashboard() {
  const email = localStorage.getItem('userEmail')

  return (
    <DashboardLayout role="student">
      <div className="dashboard-welcome">
        <h1>Student Dashboard</h1>

        <p>
          Welcome back, {email || 'Student'}!
        </p>
      </div>

      <div className="dashboard-cards">
        <div className="dashboard-card">
          <h3>My Profile</h3>
          <p>View and manage your profile information.</p>
        </div>

        <div className="dashboard-card">
          <h3>Applications</h3>
          <p>Track your submitted applications.</p>
        </div>

        <div className="dashboard-card">
          <h3>Scholarships</h3>
          <p>Explore available scholarships.</p>
        </div>

        <div className="dashboard-card">
          <h3>Internships</h3>
          <p>Find and manage internship opportunities.</p>
        </div>

        <div className="dashboard-card">
          <h3>FYP Management</h3>
          <p>Explore and manage Final Year Project ideas.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default StudentDashboard