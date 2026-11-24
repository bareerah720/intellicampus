import { useCallback, useEffect, useState } from 'react'
import {
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '../services/notificationService'

function formatDate(value) {
  return new Date(value).toLocaleString('en-PK', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function NotificationCenter() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(false)

  const loadNotifications = useCallback(async () => {
    try {
      setError('')
      const data = await fetchNotifications()
      setNotifications(data)
    } catch {
      setError('Could not load notifications. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  async function handleMarkRead(id) {
    try {
      await markNotificationRead(id)

      setNotifications((current) =>
        current.map((item) =>
          item.id === id ? { ...item, is_read: true } : item
        )
      )
    } catch {
      setError('Could not update notification. Please try again.')
    }
  }

  async function handleMarkAllRead() {
    try {
      setUpdating(true)
      await markAllNotificationsRead()

      setNotifications((current) =>
        current.map((item) => ({ ...item, is_read: true }))
      )
    } catch {
      setError('Could not mark all notifications as read.')
    } finally {
      setUpdating(false)
    }
  }

  const unreadCount = notifications.filter(
    (item) => !item.is_read
  ).length

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Recent updates</h2>
          <p>
            {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={handleMarkAllRead}
          disabled={updating || unreadCount === 0}
        >
          {updating ? 'Updating...' : 'Mark all as read'}
        </button>
      </div>

      {error && <div className="notice">{error}</div>}

      {loading ? (
        <p className="muted-note">Loading notifications...</p>
      ) : notifications.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">♧</div>
          <h3>No notifications yet</h3>
          <p>New updates about your applications will appear here.</p>
        </div>
      ) : (
        <div className="notification-list">
          {notifications.map((item) => (
            <div
              className={`notification-item ${item.is_read ? 'read' : 'unread'}`}
              key={item.id}
            >
              <span
                className={`notification-dot ${item.is_read ? '' : 'blue'}`}
              />

              <div>
                <strong>{item.title}</strong>
                <p>{item.message}</p>
                <small>{formatDate(item.created_at)}</small>
              </div>

              {!item.is_read && (
                <button
                  className="secondary-button"
                  onClick={() => handleMarkRead(item.id)}
                >
                  Mark as read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default NotificationCenter
