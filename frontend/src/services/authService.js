import { apiClient } from './apiClient'
import { tokenStorage } from './tokenStorage'

export async function fetchCurrentUser() {
  const { data } = await apiClient.get('/api/accounts/me/')
  return data
}

// Student: registration number se login. Response mein user + student dono aate hain.
export async function loginStudent({ registrationNumber, password }) {
  const { data } = await apiClient.post('/api/accounts/student-login/', {
    registration_number: registrationNumber.trim(),
    password,
  })
  tokenStorage.set({ access: data.access, refresh: data.refresh })
  return { user: data.user, student: data.student }
}

// Faculty / Staff / Admin / External Examiner: username se login.
// Ye endpoint sirf tokens deta hai, is liye user_type ke liye /me/ call hota hai.
export async function loginStaff({ username, password }) {
  const { data } = await apiClient.post('/api/auth/token/', {
    username: username.trim(),
    password,
  })
  tokenStorage.set({ access: data.access, refresh: data.refresh })

  try {
    const user = await fetchCurrentUser()
    return { user }
  } catch (error) {
    tokenStorage.clear()
    throw error
  }
}

export async function changePassword({ currentPassword, newPassword }) {
  const { data } = await apiClient.post('/api/accounts/change-password/', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}

// Backend mein token blacklist nahi hai, is liye logout client-side hai.
export function logout() {
  tokenStorage.clear()
}