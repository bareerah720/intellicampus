import {
  createContext,
  useCallback,
  useEffect,
  useState,
} from 'react'
import { apiClient, setAuthFailureHandler } from '../services/apiClient'
import {
  fetchCurrentUser,
  loginStaff,
  loginStudent,
  logout as clearSession,
} from '../services/authService'
import { tokenStorage } from '../services/tokenStorage'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [student, setStudent] = useState(null)
  const [loading, setLoading] = useState(true)

  const signOut = useCallback(() => {
    clearSession()
    setUser(null)
    setStudent(null)
  }, [])

  useEffect(() => {
    setAuthFailureHandler(signOut)

    async function restoreSession() {
      if (!tokenStorage.getAccess()) {
        setLoading(false)
        return
      }

      try {
        const currentUser = await fetchCurrentUser()
        setUser(currentUser)
      } catch {
        clearSession()
        setUser(null)
        setStudent(null)
      } finally {
        setLoading(false)
      }
    }

    restoreSession()

    return () => setAuthFailureHandler(null)
  }, [signOut])

  const signIn = useCallback(async ({ role, identifier, password }) => {
    let result

    if (role === 'student') {
      result = await loginStudent({
        registrationNumber: identifier,
        password,
      })
      setStudent(result.student)
      setUser(result.user)
      return result.user
    }

    result = await loginStaff({
      email: identifier,
      password,
    })

    setStudent(null)
    setUser(result.user)
    return result.user
  }, [])

  const changePassword = useCallback(async (payload) => {
    const { data } = await apiClient.post(
      '/api/accounts/change-password/',
      {
        current_password: payload.currentPassword,
        new_password: payload.newPassword,
      },
    )

    const updatedUser = { ...user, must_change_password: false }
    setUser(updatedUser)
    return data
  }, [user])

  const refreshCurrentUser = useCallback(async () => {
    const currentUser = await fetchCurrentUser()
    setUser(currentUser)
    return currentUser
  }, [])

  const value = {
    user,
    student,
    loading,
    isAuthenticated: Boolean(user && tokenStorage.getAccess()),
    signIn,
    signOut,
    changePassword,
    refreshCurrentUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
