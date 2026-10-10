import { Link } from 'react-router-dom'

function Home() {
  return (
    <main>
      <section>
        <h1>IntelliCampus</h1>

        <h2>University Student Portal</h2>

        <p>
          A unified platform for students, faculty, staff and administrators.
        </p>

        <div>
          <Link to="/login">
            <button type="button">Login</button>
          </Link>
        </div>
      </section>
    </main>
  )
}

export default Home