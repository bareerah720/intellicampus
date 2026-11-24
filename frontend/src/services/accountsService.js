import { apiClient } from './apiClient'

// ================================
// USER MANAGEMENT
// ================================

export async function fetchUsers() {
  const response = await apiClient.get('/api/accounts/users/')
  return response.data
}

export async function createUser(data) {
  const response = await apiClient.post('/api/accounts/users/', data)
  return response.data
}
export async function createAdminUser(data) {
  const response = await apiClient.post('/api/accounts/admin-users/', data)
  return response.data
}

export async function updateUser(id, data) {
  const response = await apiClient.patch(`/api/accounts/users/${id}/`, data)
  return response.data
}

export async function fetchAdminUserProfile(id) {
  const response = await apiClient.get(`/api/accounts/users/${id}/profile/`)
  return response.data
}

export async function fetchAdminUserManagementProfile(id) {
  const response = await apiClient.get(`/api/accounts/users/${id}/management-profile/`)
  return response.data
}

export async function updateAdminUserManagementProfile(id, data) {
  const response = await apiClient.patch(
    `/api/accounts/users/${id}/management-profile/`,
    data,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return response.data
}

export async function setAdminUserPassword(id, { newPassword, confirmPassword }) {
  const response = await apiClient.post(
    `/api/accounts/users/${id}/set-password/`,
    { new_password: newPassword, confirm_password: confirmPassword },
  )
  return response.data
}

export async function sendAdminPasswordReset(id) {
  const response = await apiClient.post(`/api/accounts/users/${id}/password-reset/`)
  return response.data
}

// ================================
// ORGANIZATION DATA
// ================================

export async function fetchDepartments() {
  const response = await apiClient.get('/api/accounts/departments/')
  return response.data
}

export async function fetchOffices() {
  const response = await apiClient.get('/api/accounts/offices/')
  return response.data
}

export async function fetchBatches() {
  const response = await apiClient.get('/api/accounts/batches/')
  return response.data
}

// ================================
// FACULTY AND STAFF PROFILES
// ================================

export async function fetchFacultyProfiles() {
  const response = await apiClient.get('/api/accounts/faculty-profiles/')
  return response.data
}

export async function createFacultyProfile(data) {
  const response = await apiClient.post('/api/accounts/faculty-profiles/', data)
  return response.data
}

export async function updateFacultyProfile(id, data) {
  const response = await apiClient.patch(`/api/accounts/faculty-profiles/${id}/`, data)
  return response.data
}

export async function fetchStaffProfiles() {
  const response = await apiClient.get('/api/accounts/staff-profiles/')
  return response.data
}

export async function createStaffProfile(data) {
  const response = await apiClient.post('/api/accounts/staff-profiles/', data)
  return response.data
}

export async function updateStaffProfile(id, data) {
  const response = await apiClient.patch(`/api/accounts/staff-profiles/${id}/`, data)
  return response.data
}

// ================================
// RESPONSIBILITY ASSIGNMENTS
// ================================

export async function fetchResponsibilities() {
  const response = await apiClient.get('/api/accounts/responsibilities/')
  return response.data
}

export async function fetchMyProfile() {
  const response = await apiClient.get('/api/accounts/me/profile/')
  return response.data
}

export async function updateMyProfile(data) {
  const response = await apiClient.patch('/api/accounts/me/profile/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function createResponsibility(data) {
  const response = await apiClient.post('/api/accounts/responsibilities/', data)
  return response.data
}

export async function updateResponsibility(id, data) {
  const response = await apiClient.patch(`/api/accounts/responsibilities/${id}/`, data)
  return response.data
}

export async function fetchPrograms() {
  const response = await apiClient.get('/api/accounts/programs/')
  return response.data
}

export async function fetchSemesters() {
  const response = await apiClient.get('/api/accounts/semesters/')
  return response.data
}

export async function fetchAcademicSessions() {
  const response = await apiClient.get('/api/accounts/academic-sessions/')
  return response.data
}

export async function fetchStudentProfiles() {
  const response = await apiClient.get('/api/accounts/student-profiles/')
  return response.data
}

export async function createStudentProfile(data) {
  const response = await apiClient.post('/api/accounts/student-profiles/', data)
  return response.data
}

export async function updateStudentProfile(id, data) {
  const response = await apiClient.patch(`/api/accounts/student-profiles/${id}/`, data)
  return response.data
}
