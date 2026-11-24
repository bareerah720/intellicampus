import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
function ProtectedRoute({ allowedRoles }) {
 const { user, loading } = useAuth()
 const location = useLocation()
 if (loading) return <div className="center-page"><div className="loading-card"><span className="loading-spinner"/>Checking your session…</div></div>
 if (!user) return <Navigate to="/login" replace/>
 if (user.must_change_password && location.pathname !== '/change-password') {
  return <Navigate to="/change-password" replace/>
 }
 if (allowedRoles && !allowedRoles.includes(user.user_type)) return <Navigate to="/unauthorized" replace/>
 return <Outlet/>
}
export default ProtectedRoute
