import './App.css'
import { Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Login from './pages/Login'
import DashboardHome from './pages/DashboardHome'
import ModulePage from './pages/ModulePage'
import NotFound from './pages/NotFound'
import ProtectedRoute from './routes/ProtectedRoute'
import RoleRedirect from './routes/RoleRedirect'
import Applications from './pages/Applications'
import AdminApplications from './pages/AdminApplications'
import WorkflowManagement from './pages/WorkflowManagement'
import ReviewApplications from './pages/ReviewApplications'
import UserManagement from './pages/UserManagement'
import AdminDashboard from './pages/AdminDashboard'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ProfilePage from './pages/ProfilePage'
import ProfileViewPage from './pages/ProfileViewPage'
import AdminUserEditPage from './pages/AdminUserEditPage'
import ChangePasswordPage from './pages/ChangePasswordPage'
function Unauthorized() {
 return <div className="center-page"><section className="auth-card"><div className="brand-mark">i</div><h1>Access restricted</h1><p>This account does not have permission to view this page.</p><Link className="primary-button" to="/dashboard">Return to dashboard</Link></section></div>
}
function App() {
 return <Routes>
  <Route path="/" element={<Home/>}/>
  <Route path="/login" element={<Login/>}/>
  <Route path="/forgot-password" element={<ForgotPassword/>}/>
  <Route path="/reset-password/:uid/:token" element={<ResetPassword/>}/>
  <Route path="/unauthorized" element={<Unauthorized/>}/>
  <Route element={<ProtectedRoute/>}>
   <Route path="/dashboard" element={<RoleRedirect/>}/>
   <Route path="/change-password" element={<ChangePasswordPage/>}/>
   <Route path="/profile" element={<ProfileViewPage/>}/>
   <Route path="/profile/edit" element={<ProfilePage/>}/>
   <Route element={<ProtectedRoute allowedRoles={['student']} />}>
    <Route path="/student-dashboard" element={<DashboardHome role="student"/>}/>
    <Route path="/applications" element={<Applications />}/>
   </Route>
   <Route element={<ProtectedRoute allowedRoles={['faculty']} />}>
    <Route path="/faculty-dashboard" element={<DashboardHome role="faculty"/>}/>
   </Route>
   <Route element={<ProtectedRoute allowedRoles={['staff']} />}>
    <Route path="/staff-dashboard" element={<DashboardHome role="staff"/>}/>
   </Route>
   <Route element={<ProtectedRoute allowedRoles={['external_examiner']} />}>
    <Route path="/examiner-dashboard" element={<DashboardHome role="external_examiner"/>}/>
   </Route>
   <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
    <Route path="/admin-dashboard" element={<AdminDashboard/>}/>
    <Route path="/admin-applications" element={<AdminApplications />} />
    <Route path="/workflows" element={<WorkflowManagement />} />
    <Route path="/users" element={<UserManagement />} />
    <Route path="/users/:id/edit" element={<AdminUserEditPage />} />
   </Route>
   <Route element={<ProtectedRoute allowedRoles={['admin', 'faculty', 'staff']} />}>
    <Route path="/review-applications" element={<ReviewApplications />}/>
   </Route>
   {['scholarships','opportunities','fyp','chatbot','notifications','analytics','knowledge-base','help'].map(page => (
    <Route key={page} path={`/${page}`} element={<ModulePage page={page} />} />
   ))}
  </Route>
  <Route path="*" element={<NotFound/>}/>
 </Routes>
}
export default App
