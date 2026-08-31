import { Link } from 'react-router-dom'

function Dashboard() {
  return (
    <main>
      <section>
        <h1>IntelliCampus</h1>

        <h2>Dashboard</h2>

        <p>Welcome to your IntelliCampus dashboard.</p>

        <div>
          <h3>Quick Access</h3>

          <ul>
            <li>Profile</li>
            <li>Applications</li>
            <li>Scholarships</li>
            <li>Internships</li>
            <li>Final Year Projects</li>
          </ul>
        </div>

        <br />

        <Link to="/">Back to Home</Link>
      </section>
    </main>
  )
}

export default Dashboard