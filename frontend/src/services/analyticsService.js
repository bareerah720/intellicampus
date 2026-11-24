import { apiClient } from './apiClient'

export async function fetchAnalytics() {
  const response = await apiClient.get('/api/applications/analytics/')
  return response.data
}
