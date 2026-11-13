export const ROLES = {
  STUDENT: 'student',
  FACULTY: 'faculty',
  STAFF: 'staff',
  ADMIN: 'admin',
  EXTERNAL_EXAMINER: 'external_examiner',
}

export const ROLE_DASHBOARDS = {
  student: '/student-dashboard',
  faculty: '/faculty-dashboard',
  staff: '/staff-dashboard',
  admin: '/admin-dashboard',
  external_examiner: '/examiner-dashboard',
}

export function getDashboardPath(user) {
  return ROLE_DASHBOARDS[user?.user_type] || '/login'
}