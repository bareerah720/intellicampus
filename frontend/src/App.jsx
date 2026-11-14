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
import ReviewApplications from './pages/ReviewApplications'
function Unauthorized() {
 return <div className="center-page"><section className="auth-card"><div className="brand-mark">i</div><h1>Access restricted</h1><p>This account does not have permission to view this page.</p><Link className="primary-button" to="/dashboard">Return to dashboard</Link></section></div>
}
function App() {
 return <Routes>
  <Route path="/" element={<Home/>}/>
  <Route path="/login" element={<Login/>}/>
  <Route path="/unauthorized" element={<Unauthorized/>}/>
  <Route element={<ProtectedRoute/>}>
   <Route path="/dashboard" element={<RoleRedirect/>}/>
   <Route path="/student-dashboard" element={<DashboardHome role="student"/>}/>
   <Route path="/faculty-dashboard" element={<DashboardHome role="faculty"/>}/>
   <Route path="/admin-dashboard" element={<DashboardHome role="admin"/>}/>
   <Route path="/staff-dashboard" element={<DashboardHome role="staff"/>}/>
   <Route path="/examiner-dashboard" element={<DashboardHome role="external_examiner"/>}/>
   <Route
  path="/review-applications"
  element={<ReviewApplications />}
/>
<Route
  path="/applications"
  element={<Applications />}
/>

{['profile','scholarships','opportunities','fyp','chatbot','notifications','analytics','users','workflows','knowledge-base','help'].map(page => (
  <Route
    key={page}
    path={`/${page}`}
    element={<ModulePage page={page} />}
  />
))}
  </Route>
  <Route path="*" element={<NotFound/>}/>
 </Routes>
}
export default App
