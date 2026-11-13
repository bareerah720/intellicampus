import { useNavigate } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import { useAuth } from '../hooks/useAuth'
function DashboardLayout({ role, children }) {
  const navigate = useNavigate()
  const { signOut } = useAuth()
  function handleLogout() { signOut(); navigate('/login', { replace: true }) }
  return <div className="app-shell"><Navbar role={role} onLogout={handleLogout}/><div className="workspace"><Sidebar role={role}/><main className="page-content">{children}<footer className="page-footer"><span>© 2026 IntelliCampus</span><span>University services, in one place.</span></footer></main></div></div>
}
export default DashboardLayout
