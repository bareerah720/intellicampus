import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import './PasswordReset.css'
import { confirmPasswordReset } from '../services/authService'
import { getErrorMessage } from '../utils/errorMessage'

export default function ResetPassword() {
  const { uid, token } = useParams()
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    if (password !== confirmation) {
      setError('The passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const result = await confirmPasswordReset({
        uid,
        token,
        newPassword: password,
        confirmPassword: confirmation,
      })
      setMessage(result.detail)
      setPassword('')
      setConfirmation('')
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="center-page">
      <section className="auth-card password-reset-card">
        <div className="brand-mark">i</div>
        <h1>Choose a new password</h1>
        <p>Use a strong password you have not used for this account before.</p>
        {!message && (
          <form className="password-reset-form" onSubmit={handleSubmit}>
            <label htmlFor="new-password">New password</label>
            <input
              id="new-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <label htmlFor="confirm-password">Confirm new password</label>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              required
            />
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? 'Saving…' : 'Reset password'}
            </button>
          </form>
        )}
        {message && <div className="notice" role="status">{message}</div>}
        <p><Link to="/login">Back to sign in</Link></p>
      </section>
    </div>
  )
}
