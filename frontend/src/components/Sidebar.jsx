import { Link } from 'react-router-dom'
import { NavLink } from 'react-router-dom'

function Sidebar({ role }) {
  const menuItems = {
    student: [
      'Dashboard',
      'My Profile',
      'Applications',
      'Scholarships',
      'Internships',
      'FYP Management'
    ],

    teacher: [
      'Dashboard',
      'My Profile',
      'Student Applications',
      'Internship Requests',
      'FYP Supervision',
      'Announcements'
    ],

    hod: [
      'Dashboard',
      'Department Overview',
      'Student Management',
      'Teacher Management',
      'Applications',
      'Reports'
    ],

    admin: [
      'Dashboard',
      'User Management',
      'Role Management',
      'System Management',
      'Reports'
    ]
  }

  const dashboardPaths = {
    student: '/student-dashboard',
    teacher: '/teacher-dashboard',
    hod: '/hod-dashboard',
    admin: '/admin-dashboard'
  }

    return (
    <aside className="sidebar">
      <h3>Menu</h3>

      <nav>
        {menuItems[role]?.map((item) => (
          <NavLink
            key={item}
            to={
              item === 'Dashboard'
                ? dashboardPaths[role]
                : '#'
            }
            className={({ isActive }) =>
              isActive ? 'sidebar-link active' : 'sidebar-link'
            }
          >
            {item}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar