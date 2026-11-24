import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  UserRound,
  FileText,
  Award,
  Briefcase,
  FolderKanban,
  MessageCircle,
  Bell,
  ClipboardList,
  GitBranch,
  Megaphone,
  BarChart3,
  BookOpen,
  ExternalLink,
  CircleHelp,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const menus = {
  student: [
    ['Overview', '/student-dashboard', LayoutDashboard],
    ['My Profile', '/profile', UserRound],
    ['Applications', '/applications', FileText],
    ['Scholarships', '/scholarships', Award],
    ['Opportunity Hub', '/opportunities', Briefcase],
    ['FYP Management', '/fyp', FolderKanban],
    ['University Chatbot', '/chatbot', MessageCircle],
    ['Notifications', '/notifications', Bell],
  ],
  faculty: [
    ['Overview', '/faculty-dashboard', LayoutDashboard],
    ['My Profile', '/profile', UserRound],
    ['Application Reviews', '/review-applications', FileText],
    ['Opportunity Hub', '/opportunities', Briefcase],
    ['FYP Supervision', '/fyp', FolderKanban],
    ['Announcements', '/notifications', Megaphone],
  ],
  staff: [
    ['Overview', '/staff-dashboard', LayoutDashboard],
    ['My Profile', '/profile', UserRound],
    ['Office Queue', '/review-applications', ClipboardList],
    ['Application Workflows', '/workflows', GitBranch],
    ['Notifications', '/notifications', Bell],
  ],
  admin: [
    ['Overview', '/admin-dashboard', LayoutDashboard],
    ['My Profile', '/profile', UserRound],
    ['User Management', '/users', UserRound],
    ['All Applications', '/admin-applications', FileText],
    ['Workflow Settings', '/workflows', GitBranch],
    ['Scholarships & Jobs', '/opportunities', Briefcase],
    ['FYP Management', '/fyp', FolderKanban],
    ['Analytics', '/analytics', BarChart3],
    ['Knowledge Base', '/knowledge-base', BookOpen],
    ['Notifications', '/notifications', Bell],
  ],
  external_examiner: [
    ['Overview', '/examiner-dashboard', LayoutDashboard],
    ['My Profile', '/profile', UserRound],
    ['FYP Evaluations', '/fyp', ClipboardList],
    ['Notifications', '/notifications', Bell],
  ],
}

function Sidebar({ role }) {
  const { user } = useAuth()
  const items = menus[role] || menus.student
  const configuredName = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
  const displayName = configuredName || (role === 'admin' ? 'Admin' : user?.username || 'Portal user')

  return (
    <aside className="sidebar">
      <div className="sidebar-caption">WORKSPACE</div>

      <nav>
        {items.map(([label, path, Icon]) => (
          <NavLink
            key={path + label}
            to={path}
            end
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'active' : ''}`
            }
          >
            <span className="nav-icon">
              <Icon size={18} strokeWidth={1.9} aria-hidden="true" />
            </span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-help">
        <div className="help-mark">
          <CircleHelp size={20} />
        </div>
        <strong>Need a hand?</strong>
        <p>Find guidance for using IntelliCampus.</p>
        <NavLink to="/help">
          Visit help centre <ExternalLink size={13} />
        </NavLink>
      </div>

      <div className="sidebar-user">
        <div className="avatar">
          {(configuredName || displayName)
            .slice(0, 1)
            .toUpperCase()}
        </div>
        <div>
          <strong>{displayName}</strong>
          <small>{role.replace('_', ' ')}</small>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
