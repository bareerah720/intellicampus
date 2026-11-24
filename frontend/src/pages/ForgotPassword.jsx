import { useState } from 'react'
import { Link } from 'react-router-dom'
import './PasswordReset.css'
import { requestPasswordReset } from '../services/authService'
import { getErrorMessage } from '../utils/errorMessage'

export default function ForgotPassword() {
  const [identifier, setIdentifier] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    setError('')
    try {
      const result = await requestPasswordReset(identifier)
      setMessage(result.detail)
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
        <h1>Forgot your password?</h1>
        <p>Students should enter their registration number. Faculty, staff and administrators should enter their university email. If the account is active, we’ll send a reset link to its registered address.</p>
        <form className="password-reset-form" onSubmit={handleSubmit}>
          <label htmlFor="reset-identifier">University email or registration number</label>
          <input
            id="reset-identifier"
            autoComplete="username"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            required
          />
          {error && <div className="form-error" role="alert">{error}</div>}
          {message && <div className="notice" role="status">{message}</div>}
          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
        <p><Link to="/login">Back to sign in</Link></p>
      </section>
    </div>
  )
}
