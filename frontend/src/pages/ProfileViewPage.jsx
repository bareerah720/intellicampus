import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import { fetchMyProfile } from '../services/accountsService'
import { getErrorMessage } from '../utils/errorMessage'
import { mediaUrl } from '../utils/mediaUrl'
import './ProfilePage.css'
import './ProfileViewPage.css'

const roleNames = {
  student: 'Student',
  faculty: 'Faculty',
  staff: 'Staff',
  admin: 'Central Admin',
  external_examiner: 'External Examiner',
}

function displayValue(value) {
  if (value === false) return 'No'
  if (value === true) return 'Yes'
  if (value === null || value === undefined || value === '') return '—'
  return value
}

function ProfileViewPage() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    fetchMyProfile()
      .then((data) => {
        if (active) setProfile(data)
      })
      .catch((requestError) => {
        if (active) setError(getErrorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const roleProfile = profile?.role_profile || {}
  const role = profile?.user_type || user?.user_type || 'student'
  const fullName = [profile?.first_name, profile?.last_name].filter(Boolean).join(' ')
  const displayName = fullName || (role === 'admin' ? 'Admin' : profile?.username || '—')
  const image = mediaUrl(profile?.profile_picture)
  const initials = displayName === '—' ? 'U' : displayName.slice(0, 1).toUpperCase()
  const responsibilities = profile?.responsibilities || []

  function detail(label, value, key = label) {
    return <div className="profile-detail" key={key}>
      <small>{label}</small>
      <strong>{displayValue(value)}</strong>
    </div>
  }

  return (
    <DashboardLayout role={user?.user_type || role}>
      <div className="application-page profile-page">
        <div className="page-heading">
          <div>
            <p className="eyebrow">ACCOUNT SETTINGS</p>
            <h1>My Profile</h1>
            <p>Your saved university and contact information.</p>
          </div>
          <Link className="primary-button" to="/profile/edit">Edit Profile</Link>
        </div>

        {error && <div className="form-error" role="alert">{error}</div>}
        {loading ? <section className="panel">Loading profile…</section> : profile && (
          <>
            <section className="panel profile-summary">
              <div className="profile-photo-wrap">
                {image ? <img className="profile-photo" src={image} alt="Saved profile" /> :
                  <div className="profile-photo profile-photo-fallback" aria-label="No profile picture">{initials}</div>}
              </div>
              <div className="profile-summary-copy">
                <p className="eyebrow">{roleNames[role] || role}</p>
                <h2>{displayName}</h2>
                <p>{displayValue(profile.email)}</p>
                {role === 'student' && <span className="status-chip approved">
                  {displayValue(roleProfile.registration_number)}
                </span>}
              </div>
            </section>

            <section className="panel">
              <div className="panel-header"><div><h2>Profile details</h2><p>University-assigned information is read-only here.</p></div></div>
              <div className="profile-detail-grid profile-view-grid">
                {detail('Name', displayName)}
                {detail('University email', profile.email)}
                {detail('Role', roleNames[role] || role)}
                {detail('Phone', profile.phone_number)}

                {role === 'student' && <>
                  {detail('Registration number', roleProfile.registration_number)}
                  {detail('Program', roleProfile.program)}
                  {detail('Batch', roleProfile.batch)}
                  {detail('Current semester', roleProfile.current_semester)}
                  {detail('Admission session', roleProfile.admission_session)}
                  {detail('CGPA', roleProfile.cgpa)}
                  {detail('Date of birth', roleProfile.date_of_birth)}
                  {detail('Gender', roleProfile.gender)}
                  {detail('Address', roleProfile.address)}
                  {detail('Emergency contact', roleProfile.emergency_contact)}
                  {detail('Guardian phone', roleProfile.guardian_phone)}
                </>}

                {['faculty', 'staff'].includes(role) && <>
                  {detail('Employee ID', roleProfile.employee_id)}
                  {role === 'faculty' && detail('Department', roleProfile.department)}
                  {detail('Office', roleProfile.office)}
                  {detail('Designation', roleProfile.designation)}
                  {role === 'faculty' && detail('Specialization', roleProfile.specialization)}
                  {detail('Joining date', role === 'staff' ? roleProfile.joining_date : null)}
                  {detail('Current responsibilities', responsibilities.length
                    ? responsibilities.map((item) => `${item.label}${item.scope ? ` · ${item.scope}` : ''}`).join('; ')
                    : null)}
                  {detail('Address', roleProfile.address)}
                </>}
              </div>
            </section>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}

export default ProfileViewPage
