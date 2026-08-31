function Navbar({ role, onLogout }) {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <h2>IntelliCampus</h2>
        <span>{role} Portal</span>
      </div>

      <button
        type="button"
        className="logout-button"
        onClick={onLogout}
      >
        Logout
      </button>
    </header>
  )
}

export default Navbar