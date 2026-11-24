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

// Faculty / Staff / Admin / External Examiner: email se login.
export async function loginStaff({ email, password }) {
  const { data } = await apiClient.post('/api/accounts/email-login/', {
    email: email.trim(),
    password,
  })

  tokenStorage.set({ access: data.access, refresh: data.refresh })

  return { user: data.user }
}

export async function requestPasswordReset(identifier) {
  const { data } = await apiClient.post('/api/accounts/password-reset/', {
    identifier: identifier.trim(),
  })
  return data
}

export async function confirmPasswordReset({ uid, token, newPassword, confirmPassword }) {
  const { data } = await apiClient.post('/api/accounts/password-reset/confirm/', {
    uid,
    token,
    new_password: newPassword,
    confirm_password: confirmPassword,
  })
  return data
}

export async function changePassword({ currentPassword, newPassword }) {
  const { data } = await apiClient.post('/api/accounts/change-password/', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}

// Logout is currently client-side because the existing JWT configuration
// has no blacklist dependency or server-side session table.
export function logout() {
  tokenStorage.clear()
}
