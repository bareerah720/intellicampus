import axios from 'axios'
import { tokenStorage } from './tokenStorage'

const BASE_URL = import.meta.env.VITE_API_BASE_URL

if (!BASE_URL) {
  console.error('VITE_API_BASE_URL is not set. Create frontend/.env (see .env.example).')
}

// Ye endpoints token ke baghair call hote hain.
const PUBLIC_PATHS = [
  '/api/auth/token/',
  '/api/auth/token/refresh/',
  '/api/accounts/student-login/',
  '/api/accounts/password-reset/',
  '/api/accounts/password-reset/confirm/',
]

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// AuthContext isko register karta hai taake session fail hone par UI logout ho jaye.
let onAuthFailure = null
export function setAuthFailureHandler(handler) {
  onAuthFailure = handler
}

// Request: public endpoints ke ilawa har request mein access token lagao.
apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token && !PUBLIC_PATHS.includes(config.url)) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Concurrent 401s par sirf ek refresh call jaye.
let refreshPromise = null

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${BASE_URL}/api/auth/token/refresh/`, {
        refresh: tokenStorage.getRefresh(),
      })
      .then(({ data }) => {
        // Backend ROTATE_REFRESH_TOKENS=True hai, naya refresh token bhi save karna zaroori hai.
        tokenStorage.set({ access: data.access, refresh: data.refresh })
        return data.access
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

// Response: 401 par ek baar refresh try karo, fail ho to session khatam.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const isPublic = original && PUBLIC_PATHS.includes(original.url)

    if (status === 401 && original && !isPublic) {
      if (!original._retry && tokenStorage.getRefresh()) {
        original._retry = true
        try {
          const newAccess = await refreshAccessToken()
          original.headers.Authorization = `Bearer ${newAccess}`
          return apiClient(original)
        } catch {
          // refresh fail, neeche session clear hoga
        }
      }
      tokenStorage.clear()
      if (onAuthFailure) onAuthFailure()
    }

    return Promise.reject(error)
  },
)
