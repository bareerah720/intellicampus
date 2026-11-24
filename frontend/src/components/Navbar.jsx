import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchUnreadCount } from '../services/notificationService'

function Navbar({ role, onLogout }) {
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    let active = true

    async function loadUnreadCount() {
      try {
        const data = await fetchUnreadCount()

        if (active) {
          setUnreadCount(data.unread_count || 0)
        }
      } catch {
        // Keep the existing count if the request temporarily fails.
      }
    }

    loadUnreadCount()

    const interval = setInterval(loadUnreadCount, 15000)

    return () => {
      active = false
      clearInterval(interval)
    }
  }, [])

  return (
    <header className="topbar">
      <Link to="/" className="brand">
        <span className="brand-mark">i</span>
        <span>
          Intelli<span className="brand-light">Campus</span>
          <small>UNIVERSITY PORTAL</small>
        </span>
      </Link>

      <div className="topbar-right">
        <span className="portal-pill">
          {(role || 'student').replace('_', ' ')} portal
        </span>

        <Link
          className="icon-button"
          to="/notifications"
          aria-label={`Notifications, ${unreadCount} unread`}
        >
          <span aria-hidden="true">&#128276;</span>

          {unreadCount > 0 && (
            <span className="notification-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Link>

        <button
          type="button"
          className="logout-button"
          onClick={onLogout}
        >
          Sign out <span>&#8599;</span>
        </button>
      </div>
    </header>
  )
}

export default Navbar
