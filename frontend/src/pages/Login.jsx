import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

function Login() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(event) {
    event.preventDefault()

    if (!email.trim()) {
      alert('Please enter your email')
      return
    }

    if (!password) {
      alert('Please enter your password')
      return
    }

    if (password.length < 8) {
      alert('Password must be at least 8 characters long')
      return
    }

    // Temporary testing login
    console.log('Login successful for:', email)

    localStorage.setItem('userEmail', email)
    localStorage.setItem('userRole', 'student')

    navigate('/student-dashboard')
  }

  return (
    <main>
      <section>
        <h1>IntelliCampus</h1>

        <h2>Welcome Back</h2>

        <p>Login to access your account</p>

        <form onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email">Email Address</label>

            <input
              type="email"
              id="email"
              name="email"
              placeholder="Enter your email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="password">Password</label>

            <input
              type="password"
              id="password"
              name="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <button type="submit">Login</button>
        </form>

        <p>
          Don't have an account?{' '}
          <Link to="/register">Create an account</Link>
        </p>

        <Link to="/">Back to Home</Link>
      </section>
    </main>
  )
}

export default Login