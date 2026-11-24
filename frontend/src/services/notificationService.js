import { apiClient } from './apiClient'

// Fetch notifications for the logged-in user
export async function fetchNotifications() {
  const response = await apiClient.get('/api/notifications/')
  return response.data
}

// Fetch unread notification count
export async function fetchUnreadCount() {
  const response = await apiClient.get('/api/notifications/unread-count/')
  return response.data
}

// Mark one notification as read
export async function markNotificationRead(id) {
  const response = await apiClient.post(
    `/api/notifications/${id}/mark-read/`
  )
  return response.data
}

// Mark all notifications as read
export async function markAllNotificationsRead() {
  const response = await apiClient.post(
    '/api/notifications/mark-all-read/'
  )
  return response.data
}
