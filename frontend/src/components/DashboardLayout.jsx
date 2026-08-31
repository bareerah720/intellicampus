import { useNavigate } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

function DashboardLayout({ role, children }) {
  const navigate = useNavigate()

  function handleLogout() {
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userRole')

    navigate('/login')
  }

  return (
    <div className="dashboard-layout">
      <Navbar
        role={role}
        onLogout={handleLogout}
      />

      <div className="dashboard-body">
        <Sidebar role={role} />

        <main className="dashboard-content">
          {children}
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout