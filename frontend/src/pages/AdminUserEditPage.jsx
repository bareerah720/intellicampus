import { useEffect, useLayoutEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import {
  fetchAcademicSessions,
  fetchAdminUserManagementProfile,
  fetchBatches,
  fetchDepartments,
  fetchOffices,
  fetchPrograms,
  fetchSemesters,
  updateAdminUserManagementProfile,
} from '../services/accountsService'
import { getErrorMessage } from '../utils/errorMessage'
import { mediaUrl } from '../utils/mediaUrl'
import './AdminUserEditPage.css'

const emptyRecord = {
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  profile_picture: '',
  role_profile: {},
  responsibilities: [],
}

const rows = (value) => Array.isArray(value) ? value : value?.results || []

function batchMatches(batch, programId, session) {
  if (!batch || String(batch.program) !== String(programId)) return false
  if (!session) return true
  const year = Number(session.start_date.slice(0, 4))
  const prefix = session.session_type === 'spring' ? 'Sp' : 'Fa'
  return batch.admission_year === year
    && batch.name?.toLowerCase() === `${prefix}${String(year).slice(-2)}`.toLowerCase()
}

function profileFormData(profile) {
  return {
    first_name: profile.first_name || '',
    last_name: profile.last_name || '',
    email: profile.email || '',
    phone_number: profile.phone_number || '',
    ...(profile.role_profile || {}),
  }
}

function AdminUserEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [profile, setProfile] = useState(emptyRecord)
  const [form, setForm] = useState({})
  const [options, setOptions] = useState({
    programs: [], batches: [], semesters: [], sessions: [], departments: [], offices: [],
  })
  const [photo, setPhoto] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useLayoutEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
    document.querySelector('.page-content')?.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }, [id])

  useEffect(() => {
    let active = true
    setLoading(true)
    Promise.all([
      fetchAdminUserManagementProfile(id),
      fetchPrograms(),
      fetchBatches(),
      fetchSemesters(),
      fetchAcademicSessions(),
      fetchDepartments(),
      fetchOffices(),
    ]).then(([userProfile, programs, batches, semesters, sessions, departments, offices]) => {
      if (!active) return
      setProfile(userProfile)
      setForm(profileFormData(userProfile))
      setOptions({
        programs: rows(programs),
        batches: rows(batches),
        semesters: rows(semesters),
        sessions: rows(sessions),
        departments: rows(departments),
        offices: rows(offices),
      })
    }).catch((requestError) => {
      if (active) setError(getErrorMessage(requestError))
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [id])

  const currentRole = profile.user_type
  const profileName = [profile.first_name, profile.last_name].filter(Boolean).join(' ')
    || (currentRole === 'admin' ? 'Admin' : profile.username || '—')
  const selectedProgram = options.programs.find((item) => String(item.id) === String(form.program))
  const selectedSession = options.sessions.find((item) => String(item.id) === String(form.academic_session))
  const effectiveSemesterCount = selectedProgram?.effective_semester_count
    ?? ((selectedProgram?.duration_years || 0) * 2)
  const validSemesters = useMemo(() => options.semesters.filter((item) =>
    item.number <= effectiveSemesterCount
  ), [options.semesters, effectiveSemesterCount])
  const currentSemester = options.semesters.find((item) => String(item.id) === String(form.current_semester))
  const availableSemesters = currentSemester && !validSemesters.some((item) => item.id === currentSemester.id)
    ? [...validSemesters, currentSemester]
    : validSemesters
  const validBatches = useMemo(() => options.batches.filter((item) =>
    batchMatches(item, form.program, selectedSession)
  ), [options.batches, form.program, selectedSession])
  const currentBatch = options.batches.find((item) => String(item.id) === String(form.batch))
  const availableBatches = currentBatch && !validBatches.some((item) => item.id === currentBatch.id)
    ? [...validBatches, currentBatch]
    : validBatches
  const savedPhoto = mediaUrl(profile.profile_picture)
  const initials = profileName === '—' ? 'U' : profileName[0]

  function setField(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  function handleChange(event) {
    const { name, value } = event.target
    if (name === 'program') {
      const nextProgram = options.programs.find((item) => String(item.id) === String(value))
      const nextCount = nextProgram?.effective_semester_count ?? ((nextProgram?.duration_years || 0) * 2)
      setForm((previous) => {
        const previousBatch = options.batches.find((item) => String(item.id) === String(previous.batch))
        const previousSemester = options.semesters.find((item) => String(item.id) === String(previous.current_semester))
        return {
          ...previous,
          program: value,
          batch: batchMatches(previousBatch, value, selectedSession) ? previous.batch : '',
          current_semester: previousSemester && previousSemester.number <= nextCount ? previous.current_semester : '',
        }
      })
    } else if (name === 'academic_session') {
      const nextSession = options.sessions.find((item) => String(item.id) === String(value))
      setForm((previous) => {
        const previousBatch = options.batches.find((item) => String(item.id) === String(previous.batch))
        return {
          ...previous,
          academic_session: value,
          batch: batchMatches(previousBatch, previous.program, nextSession) ? previous.batch : '',
        }
      })
    } else {
      setField(name, value)
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const payload = new FormData()
      const commonFields = ['first_name', 'last_name', 'email', 'phone_number']
      commonFields.forEach((field) => payload.append(field, form[field] || ''))

      const roleFields = {
        student: [
          'registration_number', 'program', 'batch', 'current_semester', 'academic_session',
          'cgpa', 'date_of_birth', 'gender', 'address', 'emergency_contact', 'guardian_phone',
        ],
        faculty: [
          'employee_id', 'department', 'designation', 'address', 'specialization', 'office',
          'email_extension', 'is_available_for_supervision', 'max_fyp_groups',
        ],
        staff: [
          'employee_id', 'office', 'designation', 'address', 'joining_date', 'staff_profile_is_active',
        ],
      }[currentRole] || []

      roleFields.forEach((field) => {
        const value = form[field]
        payload.append(field, value === null || value === undefined ? '' : String(value))
      })
      if (photo) payload.append('profile_picture', photo)

      const updated = await updateAdminUserManagementProfile(id, payload)
      setProfile(updated)
      setForm(profileFormData(updated))
      setPhoto(null)
      setNotice('User profile updated successfully.')
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  function selectField(name, label, values, getLabel, placeholder = 'Select…') {
    return <label className="admin-edit-field" key={name}>
      <span>{label}</span>
      <select name={name} value={form[name] ?? ''} onChange={handleChange}>
        <option value="">{placeholder}</option>
        {values.map((item) => <option key={item.id} value={item.id}>{getLabel(item)}</option>)}
      </select>
    </label>
  }

  function textField(name, label, type = 'text', options = {}) {
    return <label className={`admin-edit-field ${options.wide ? 'wide-field' : ''}`} key={name}>
      <span>{label}</span>
      {type === 'textarea' ?
        <textarea name={name} value={form[name] ?? ''} onChange={handleChange} rows={3} placeholder="—" /> :
          <input
            type={type}
            name={name}
            value={form[name] ?? ''}
            onChange={handleChange}
            placeholder="—"
            min={options.min}
            max={options.max}
            step={options.step}
            required={options.required}
          />}
    </label>
  }

  function readonlyField(label, value, key = label) {
    return <div className="admin-edit-field admin-readonly-field" key={key}>
      <span>{label}</span><strong>{value || '—'}</strong>
    </div>
  }

  return (
    <DashboardLayout role={user?.user_type || 'admin'}>
      <div className="application-page admin-user-edit-page">
        <div className="page-heading">
          <div>
            <p className="eyebrow">USER MANAGEMENT</p>
            <h1>Edit user profile</h1>
            <p>University identity and role profile details.</p>
          </div>
          <button className="secondary-button" type="button" onClick={() => navigate('/users')}>Cancel</button>
        </div>

        {notice && <div className="notice" role="status">{notice}</div>}
        {error && <div className="form-error" role="alert">{error}</div>}
        {loading ? <section className="panel">Loading user profile…</section> : (
          <form className="panel admin-edit-form" onSubmit={handleSubmit}>
            <div className="admin-edit-identity">
              {savedPhoto ? <img src={savedPhoto} alt="Saved user profile" /> :
                <div className="admin-edit-photo-fallback">{initials.toUpperCase()}</div>}
              <div><h2>{profileName}</h2>
                <p>{profile.email || '—'} · {String(currentRole || '').replaceAll('_', ' ')}</p></div>
            </div>

            <section className="admin-edit-section">
              <h2>Account information</h2>
              <div className="admin-edit-grid">
                {textField('first_name', 'First name')}
                {textField('last_name', 'Last name')}
                {textField('email', 'University email', 'email')}
                {readonlyField('Role', String(currentRole || '').replaceAll('_', ' '))}
                {textField('phone_number', 'Phone number', 'tel')}
                <label className="admin-edit-field">
                  <span>Profile picture</span>
                  <input type="file" accept="image/*" onChange={(event) => setPhoto(event.target.files?.[0] || null)} />
                </label>
              </div>
            </section>

            {currentRole === 'student' && <section className="admin-edit-section">
              <h2>Student information</h2>
              <div className="admin-edit-grid">
                {textField('registration_number', 'Registration number')}
                {selectField('program', 'Program', options.programs, (item) => `${item.name} (${item.code})`)}
                {selectField('batch', 'Batch', availableBatches, (item) => `${item.name} · ${item.admission_year}`)}
                {selectField('current_semester', 'Current semester', availableSemesters, (item) => item.title)}
                {selectField('academic_session', 'Admission session', options.sessions, (item) => item.title)}
                {textField('cgpa', 'CGPA', 'number', { min: 0, max: 4, step: '0.01', required: true })}
                {textField('date_of_birth', 'Date of birth', 'date')}
                <label className="admin-edit-field"><span>Gender</span>
                  <select name="gender" value={form.gender ?? ''} onChange={handleChange}>
                    <option value="">—</option><option value="female">Female</option><option value="male">Male</option>
                  </select>
                </label>
                {textField('address', 'Address', 'textarea', { wide: true })}
                {textField('emergency_contact', 'Emergency contact', 'tel')}
                {textField('guardian_phone', 'Guardian phone', 'tel')}
              </div>
            </section>}

            {currentRole === 'faculty' && <section className="admin-edit-section">
              <h2>Faculty information</h2>
              <div className="admin-edit-grid">
                {textField('employee_id', 'Employee ID')}
                {selectField('department', 'Department', options.departments, (item) => item.name)}
                {textField('designation', 'Designation')}
                {textField('specialization', 'Specialization')}
                {selectField('office', 'Office', options.offices, (item) => item.name, 'No office')}
                {textField('email_extension', 'Email extension')}
                {textField('max_fyp_groups', 'Maximum FYP groups', 'number', { min: 1, step: 1, required: true })}
                <label className="admin-edit-field admin-checkbox-field"><span>Available for supervision</span>
                  <input type="checkbox" checked={Boolean(form.is_available_for_supervision)} onChange={(event) => setField('is_available_for_supervision', event.target.checked)} />
                </label>
                {readonlyField('Joining date', null)}
                {textField('address', 'Address', 'textarea', { wide: true })}
              </div>
            </section>}

            {currentRole === 'staff' && <section className="admin-edit-section">
              <h2>Staff information</h2>
              <div className="admin-edit-grid">
                {textField('employee_id', 'Employee ID')}
                {selectField('office', 'Office', options.offices, (item) => item.name)}
                {textField('designation', 'Designation')}
                {textField('joining_date', 'Joining date', 'date')}
                <label className="admin-edit-field admin-checkbox-field"><span>Staff profile active</span>
                  <input type="checkbox" checked={Boolean(form.staff_profile_is_active)} onChange={(event) => setField('staff_profile_is_active', event.target.checked)} />
                </label>
                {textField('address', 'Address', 'textarea', { wide: true })}
              </div>
            </section>}

            {['faculty', 'staff'].includes(currentRole) && <section className="admin-edit-section">
              <h2>Current responsibilities</h2>
              {(profile.responsibilities || []).length ? <ul className="admin-edit-responsibilities">
                {profile.responsibilities.map((item, index) => <li key={`${item.type}-${index}`}>
                  <strong>{item.label}</strong>{item.scope ? ` · ${item.scope}` : ''}
                </li>)}
              </ul> : <p className="muted-note">—</p>}
              <Link className="text-link" to="/workflows">Manage responsibility assignments</Link>
            </section>}

            <div className="admin-edit-actions">
              <button className="primary-button" type="submit" disabled={saving}>
                {saving ? 'Saving…' : 'Save changes'}
              </button>
              <button className="secondary-button" type="button" onClick={() => navigate('/users')}>Cancel</button>
            </div>
          </form>
        )}
      </div>
    </DashboardLayout>
  )
}

export default AdminUserEditPage
