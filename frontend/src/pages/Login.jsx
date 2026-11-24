import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getDashboardPath, ROLES } from '../config/roles'
import { getErrorMessage } from '../utils/errorMessage'
function Login() {
 const navigate=useNavigate()
 const {signIn,signOut}=useAuth()
 const [role,setRole]=useState(ROLES.STUDENT)
 const [identifier,setIdentifier]=useState('')
 const [password,setPassword]=useState('')
 const [error,setError]=useState('')
 const [submitting,setSubmitting]=useState(false)
 async function handleSubmit(e){
  e.preventDefault();setError('')
  if(!identifier.trim()||!password){setError('Please enter your login details.');return}
  setSubmitting(true)
  try{
   const user=await signIn({role,identifier,password})
   if(user.user_type!==role){signOut();setError('The selected account type does not match this account.');return}
   navigate(getDashboardPath(user),{replace:true})
  }catch(err){setError(getErrorMessage(err))}finally{setSubmitting(false)}
 }
 const isStudent=role===ROLES.STUDENT
 return <div className="login-page"><div className="login-side"><Link to="/" className="brand"><span className="brand-mark">i</span><span>Intelli<span className="brand-light">Campus</span><small>UNIVERSITY PORTAL</small></span></Link><div className="login-promo"><div className="eyebrow"><span className="eyebrow-line"/> WELCOME TO YOUR CAMPUS</div><h1>One portal.<br/><span>Every possibility.</span></h1><p>Access student services, academic opportunities and university support from one connected space.</p><div className="login-promo-art"><div className="promo-ring"/><div className="promo-square">i<span>✦</span></div><div className="promo-caption">A smarter campus experience</div></div></div><div className="login-side-footer">© 2026 IntelliCampus · University services, simplified.</div></div><div className="login-form-side"><div className="login-form-wrap"><Link to="/" className="mobile-brand brand"><span className="brand-mark">i</span><span>Intelli<span className="brand-light">Campus</span></span></Link><div className="login-kicker">YOUR CAMPUS, CONNECTED</div><h2>Welcome back</h2><p className="login-subtitle">Sign in to continue to your university portal.</p><form className="login-form" onSubmit={handleSubmit}><label htmlFor="role">Account type<select id="role" value={role} onChange={e=>{setRole(e.target.value);setIdentifier('');setError('')}}><option value={ROLES.STUDENT}>Student</option><option value={ROLES.FACULTY}>Faculty</option><option value={ROLES.STAFF}>Staff</option><option value={ROLES.ADMIN}>Administrator</option><option value={ROLES.EXTERNAL_EXAMINER}>External Examiner</option></select></label><label htmlFor="identifier">{isStudent?'Registration number':'Email Address'}<input id="identifier" autoComplete="username" value={identifier} onChange={e=>setIdentifier(e.target.value)} placeholder={isStudent?'e.g. FA21-BSE-001':'Enter your university email address'} required/></label><label htmlFor="password">Password<input id="password" type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter your password" required/></label>{error&&<div className="form-error" role="alert">{error}</div>}<button className="primary-button login-submit" type="submit" disabled={submitting}>{submitting?'Signing in…':'Sign in to IntelliCampus'} <span>→</span></button></form><p className="login-back"><Link to="/forgot-password">Forgot your password?</Link></p><div className="login-security"><span>▣</span><p>Your account is protected by secure authentication.</p></div><p className="login-back"><Link to="/">← Back to homepage</Link></p></div></div></div>
}
export default Login
