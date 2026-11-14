import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getDashboardPath } from '../config/roles'

function RoleRedirect() {
  const { user, loading } = useAuth()

  if (loading) {
    return <p>Loading your dashboard...</p>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Navigate to={getDashboardPath(user)} replace />
}

export default RoleRedirect