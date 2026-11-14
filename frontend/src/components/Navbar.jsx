import { Link } from 'react-router-dom'
function Navbar({ role, onLogout }) {
  return <header className="topbar">
    <Link to="/" className="brand"><span className="brand-mark">i</span><span>Intelli<span className="brand-light">Campus</span><small>UNIVERSITY PORTAL</small></span></Link>
    <div className="topbar-right"><span className="portal-pill">{(role || 'student').replace('_',' ')} portal</span><Link className="icon-button" to="/notifications" aria-label="Notifications">♧<i /></Link><button type="button" className="logout-button" onClick={onLogout}>Sign out <span>↗</span></button></div>
  </header>
}
export default Navbar
