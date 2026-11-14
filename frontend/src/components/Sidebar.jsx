import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const menus = {
  student: [
    ['Overview', '/student-dashboard', '◫'],
    ['My Profile', '/profile', '♙'],
    ['Applications', '/applications', '▤'],
    ['Scholarships', '/scholarships', '✦'],
    ['Opportunity Hub', '/opportunities', '↗'],
    ['FYP Management', '/fyp', '⌘'],
    ['University Chatbot', '/chatbot', '✳'],
    ['Notifications', '/notifications', '♧'],
  ],
  faculty: [
    ['Overview', '/faculty-dashboard', '◫'],
    ['My Profile', '/profile', '♙'],
    ['Application Reviews', '/review-applications', '▤'],
    ['Opportunity Hub', '/opportunities', '↗'],
    ['FYP Supervision', '/fyp', '⌘'],
    ['Announcements', '/notifications', '♧'],
  ],
  staff: [
    ['Overview', '/staff-dashboard', '◫'],
    ['Office Queue', '/review-applications', '▤'],
    ['Application Workflows', '/workflows', '⇢'],
    ['Notifications', '/notifications', '♧'],
  ],
  admin: [
    ['Overview', '/admin-dashboard', '◫'],
    ['User Management', '/users', '♙'],
    ['All Applications', '/applications', '▤'],
    ['Workflow Settings', '/workflows', '⇢'],
    ['Scholarships & Jobs', '/opportunities', '↗'],
    ['FYP Management', '/fyp', '⌘'],
    ['Analytics', '/analytics', '▥'],
    ['Knowledge Base', '/knowledge-base', '✳'],
    ['Notifications', '/notifications', '♧'],
  ],
  external_examiner: [
    ['Overview', '/examiner-dashboard', '◫'],
    ['FYP Evaluations', '/fyp', '⌘'],
    ['Notifications', '/notifications', '♧'],
  ],
}
function Sidebar({ role }) {
  const { user } = useAuth()
  const items = menus[role] || menus.student
  return <aside className="sidebar">
    <div className="sidebar-caption">WORKSPACE</div>
    <nav>{items.map(([label, path, icon]) => <NavLink key={path + label} to={path} end className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}><span className="nav-icon">{icon}</span><span>{label}</span></NavLink>)}</nav>
    <div className="sidebar-help"><div className="help-mark">?</div><strong>Need a hand?</strong><p>Find guidance for using IntelliCampus.</p><NavLink to="/help">Visit help centre ↗</NavLink></div>
    <div className="sidebar-user"><div className="avatar">{(user?.first_name || user?.username || 'U').slice(0,1).toUpperCase()}</div><div><strong>{user?.first_name || user?.username || 'Portal user'}</strong><small>{role.replace('_',' ')}</small></div></div>
  </aside>
}
export default Sidebar
