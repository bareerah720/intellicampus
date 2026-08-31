import { Link } from 'react-router-dom'

function Home() {
  return (
    <main>
      <section>
        <h1>IntelliCampus</h1>

        <h2>University Student Portal</h2>

        <p>
          A unified platform for students, teachers, HODs and administrators.
        </p>

        <div>
          <Link to="/login">
            <button type="button">Login</button>
          </Link>
        </div>

        <br />

        <div>
          <Link to="/register">
            <button type="button">Create Account</button>
          </Link>
        </div>
      </section>
    </main>
  )
}

export default Home