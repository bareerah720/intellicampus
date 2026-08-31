import { useState } from 'react'
import { Link } from 'react-router-dom'

function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [role, setRole] = useState('student')

function handleSubmit(event) {
  event.preventDefault()

  if (!username.trim()) {
    alert('Please enter your username')
    return
  }

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

  if (password !== confirmPassword) {
    alert('Passwords do not match')
    return
  }

  console.log('Registration data:')
  console.log('Username:', username)
  console.log('Email:', email)
  console.log('Password:', password)
  console.log('Role:', role)
}

  return (
    <main>
      <section>
        <h1>IntelliCampus</h1>

        <h2>Create Account</h2>

        <p>Register for your IntelliCampus account</p>

        <form onSubmit={handleSubmit}>

          <div>
            <label htmlFor="username">Username</label>

            <input
              type="text"
              id="username"
              name="username"
              placeholder="Enter your username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="email">Email</label>

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
              placeholder="Create a password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="confirmPassword">Confirm Password</label>

            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="role">Role</label>

            <select
              id="role"
              name="role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
              <option value="hod">HOD</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <button type="submit">Create Account</button>

        </form>

        <p>
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </section>
    </main>
  )
}

export default Register