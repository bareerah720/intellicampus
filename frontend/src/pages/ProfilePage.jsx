import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import { fetchMyProfile, updateMyProfile } from '../services/accountsService'
import { getErrorMessage } from '../utils/errorMessage'
import { mediaUrl } from '../utils/mediaUrl'
import './ProfilePage.css'

const roleNames = {
  student: 'Student',
  faculty: 'Faculty',
  staff: 'Staff',
  admin: 'Central Admin',
  external_examiner: 'External Examiner',
}

const studentEditableFields = [
  ['date_of_birth', 'Date of birth', 'date'],
  ['gender', 'Gender', 'select'],
  ['address', 'Address', 'textarea'],
  ['emergency_contact', 'Emergency contact', 'text'],
  ['guardian_phone', 'Guardian phone', 'text'],
]

function displayValue(value) {
  if (value === false) return 'No'
  if (value === true) return 'Yes'
  if (value === null || value === undefined || value === '') return '—'
  return value
}

function ProfilePage() {
  const navigate = useNavigate()
  const { user, refreshCurrentUser } = useAuth()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({})
  const [photo, setPhoto] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    fetchMyProfile()
      .then((data) => {
        if (!active) return
        setProfile(data)
        setForm({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          phone_number: data.phone_number || '',
          ...(data.role_profile || {}),
        })
      })
      .catch((requestError) => {
        if (active) setError(getErrorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  function handleFieldChange(event) {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  async function saveProfile(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = new FormData()
      payload.append('phone_number', form.phone_number || '')
      if (profile.user_type === 'admin') {
        payload.append('first_name', form.first_name || '')
        payload.append('last_name', form.last_name || '')
      }
      if (profile.user_type === 'student') {
        studentEditableFields.forEach(([name]) => payload.append(name, form[name] ?? ''))
      }
      if (['faculty', 'staff'].includes(profile.user_type)) {
        payload.append('address', form.address || '')
      }
      if (photo) payload.append('profile_picture', photo)
      await updateMyProfile(payload)
      await refreshCurrentUser().catch(() => {})
      navigate('/profile', { replace: true, state: { refreshedAt: Date.now() } })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  const roleProfile = profile?.role_profile || {}
  const image = mediaUrl(profile?.profile_picture)
  const configuredName = [profile?.first_name, profile?.last_name].filter(Boolean).join(' ')
  const displayName = configuredName || (profile?.user_type === 'admin' ? 'Admin' : profile?.username || '—')
  const initials = displayName === '—' ? 'U' : displayName[0]
  const student = profile?.user_type === 'student'
  const employee = ['faculty', 'staff'].includes(profile?.user_type)
  const responsibilities = profile?.responsibilities || []

  function readonlyField(label, value, key = label) {
    return <div className="profile-detail" key={key}>
      <small>{label}</small>
      <strong>{displayValue(value)}</strong>
    </div>
  }

  function editableField(name, label, type = 'text') {
    const value = form[name] ?? ''
    return <label className={`profile-detail profile-editable ${type === 'textarea' ? 'full-field' : ''}`} key={name}>
      <small>{label}</small>
      {type === 'textarea' ?
        <textarea name={name} value={value} onChange={handleFieldChange} rows={3} placeholder="—" /> :
        type === 'select' ? <select name={name} value={value} onChange={handleFieldChange}>
          <option value="">—</option>
          <option value="female">Female</option>
          <option value="male">Male</option>
        </select> :
          <input type={type} name={name} value={value} onChange={handleFieldChange} placeholder="—" />}
    </label>
  }

  return (
    <DashboardLayout role={user?.user_type || 'student'}>
      <div className="application-page profile-page">
        <div className="page-heading">
          <div>
            <p className="eyebrow">ACCOUNT SETTINGS</p>
            <h1>Edit Profile</h1>
            <p>Update permitted personal details and your profile picture.</p>
          </div>
          <button className="secondary-button" type="button" onClick={() => navigate('/profile')}>Cancel</button>
        </div>

        {error && <div className="form-error" role="alert">{error}</div>}
        {loading ? <section className="panel">Loading profile…</section> : profile && (
          <>
            <section className="panel profile-summary">
              <div className="profile-photo-wrap">
                {image ? <img className="profile-photo" src={image} alt="Saved profile" /> :
                  <div className="profile-photo profile-photo-fallback" aria-label="No profile picture">{initials.toUpperCase()}</div>}
                <label className="photo-picker">
                  Change picture
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(event) => setPhoto(event.target.files?.[0] || null)}
                  />
                </label>
                {photo && <small>{photo.name}</small>}
              </div>
              <div className="profile-summary-copy">
                <p className="eyebrow">{roleNames[profile.user_type] || profile.user_type}</p>
                <h2>{displayName}</h2>
                <p>{displayValue(profile.email)}</p>
                {student && <span className="status-chip approved">{displayValue(roleProfile.registration_number)}</span>}
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <div><h2>Profile information</h2><p>University email, role and assigned identity fields are read-only.</p></div>
              </div>
              <form className="profile-detail-grid" onSubmit={saveProfile}>
                {profile.user_type === 'admin' ? <>
                  {editableField('first_name', 'First name')}
                  {editableField('last_name', 'Last name')}
                </> : readonlyField('Name', displayName)}
                {readonlyField('University email', profile.email)}
                {readonlyField('Role', roleNames[profile.user_type] || profile.user_type)}
                {editableField('phone_number', 'Phone number')}

                {student && <>
                  {readonlyField('Registration number', roleProfile.registration_number)}
                  {readonlyField('Program', roleProfile.program)}
                  {readonlyField('Batch', roleProfile.batch)}
                  {readonlyField('Current semester', roleProfile.current_semester)}
                  {readonlyField('Admission session', roleProfile.admission_session)}
                  {readonlyField('CGPA', roleProfile.cgpa)}
                  {editableField('date_of_birth', 'Date of birth', 'date')}
                  {editableField('gender', 'Gender', 'select')}
                  {editableField('address', 'Address', 'textarea')}
                  {editableField('emergency_contact', 'Emergency contact')}
                  {editableField('guardian_phone', 'Guardian phone')}
                </>}

                {employee && <>
                  {readonlyField('Employee ID', roleProfile.employee_id)}
                  {profile.user_type === 'faculty' && readonlyField('Department', roleProfile.department)}
                  {readonlyField('Office', roleProfile.office)}
                  {readonlyField('Designation', roleProfile.designation)}
                  {profile.user_type === 'faculty' && readonlyField('Specialization', roleProfile.specialization)}
                  {readonlyField('Joining date', profile.user_type === 'staff' ? roleProfile.joining_date : null)}
                  {editableField('address', 'Address', 'textarea')}
                  <div className="profile-detail profile-responsibilities">
                    <small>Current responsibilities</small>
                    {responsibilities.length ? <ul>{responsibilities.map((item, index) => <li key={`${item.type}-${index}`}>
                      <strong>{item.label}</strong>{item.scope && <span> · {item.scope}</span>}
                    </li>)}</ul> : <strong>—</strong>}
                  </div>
                </>}

                <div className="full-field profile-form-actions">
                  <button className="primary-button" type="submit" disabled={saving}>
                    {saving ? 'Saving…' : 'Save profile'}
                  </button>
                  <button className="secondary-button" type="button" onClick={() => navigate('/profile')}>Cancel</button>
                </div>
              </form>
            </section>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}

export default ProfilePage
