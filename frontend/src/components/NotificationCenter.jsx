import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
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
  const navigate = useNavigate()
  const { user } = useAuth()
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

  function getApplicationListPath() {
    if (user?.user_type === 'student') return '/applications'
    if (['faculty', 'staff'].includes(user?.user_type)) return '/review-applications'
    return null
  }

  async function handleNotificationClick(item) {
    const applicationId = item.related_application ?? item.related_application_id
    const isApplicationNotification = item.notification_type?.startsWith('application_')
      || item.notification_type === 'revision_required'
      || applicationId !== null && applicationId !== undefined && applicationId !== ''

    if (!isApplicationNotification) return

    if (!item.is_read) await handleMarkRead(item.id)

    const destination = getApplicationListPath()
    if (!destination) return

    navigate(destination, {
      state: applicationId === null || applicationId === undefined || applicationId === ''
        ? undefined
        : { applicationId },
    })
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

              {item.notification_type?.startsWith('application_')
                || item.notification_type === 'revision_required'
                || item.related_application !== null && item.related_application !== undefined ? (
                  <button
                    type="button"
                    onClick={() => handleNotificationClick(item)}
                    style={{
                      flex: 1,
                      padding: 0,
                      border: 0,
                      background: 'transparent',
                      color: 'inherit',
                      textAlign: 'left',
                    }}
                  >
                    <strong>{item.title}</strong>
                    <p>{item.message}</p>
                    <small>{formatDate(item.created_at)}</small>
                  </button>
                ) : (
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.message}</p>
                    <small>{formatDate(item.created_at)}</small>
                  </div>
                )}

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
