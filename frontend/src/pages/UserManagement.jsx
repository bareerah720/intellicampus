import { useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import { AuthContext } from '../context/AuthContext'
import {
  fetchUsers,
  createAdminUser,
  updateUser,
  sendAdminPasswordReset,
  fetchAdminUserProfile,
  setAdminUserPassword,
  fetchPrograms,
  fetchBatches,
  fetchSemesters,
  fetchAcademicSessions,
  fetchDepartments,
  fetchOffices,
} from '../services/accountsService'
import { mediaUrl } from '../utils/mediaUrl'

const emptyForm = {
  first_name: '',
  last_name: '',
  email: '',
  user_type: 'student',
  phone_number: '',
  password: '',

  program: '',
  batch: '',
  current_semester: '',
  academic_session: '',

  employee_id: '',
  department: '',
  designation: '',
  specialization: '',
  office: '',
}

function getErrorMessage(error) {
  const data = error?.response?.data

  if (!data) return 'Something went wrong. Please try again.'
  if (typeof data === 'string') return data

  return Object.entries(data)
    .map(([field, messages]) => {
      const text = Array.isArray(messages) ? messages.join(', ') : String(messages)
      return `${field}: ${text}`
    })
    .join(' | ')
}

function UserManagement() {
  const navigate = useNavigate()
  const { user, signOut } = useContext(AuthContext)

  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [showForm, setShowForm] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [resetSendingId, setResetSendingId] = useState(null)
  const [profileUser, setProfileUser] = useState(null)
  const [profileDetails, setProfileDetails] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [passwordResetUser, setPasswordResetUser] = useState(null)
  const [passwordResetForm, setPasswordResetForm] = useState({
    newPassword: '',
    confirmPassword: '',
  })
  const [passwordResetSaving, setPasswordResetSaving] = useState(false)

  const [formOptions, setFormOptions] = useState({
    programs: [],
    batches: [],
    semesters: [],
    academicSessions: [],
    departments: [],
    offices: [],
  })

  const loadFormOptions = useCallback(async () => {
    try {
      const [
        programs,
        batches,
        semesters,
        academicSessions,
        departments,
        offices,
      ] = await Promise.all([
        fetchPrograms(),
        fetchBatches(),
        fetchSemesters(),
        fetchAcademicSessions(),
        fetchDepartments(),
        fetchOffices(),
      ])

      const normalize = (data) =>
        Array.isArray(data) ? data : data?.results || []

      setFormOptions({
        programs: normalize(programs),
        batches: normalize(batches),
        semesters: normalize(semesters),
        academicSessions: normalize(academicSessions),
        departments: normalize(departments),
        offices: normalize(offices),
      })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }, [])

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const data = await fetchUsers()
      setUsers(Array.isArray(data) ? data : data?.results || [])
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUsers()
    loadFormOptions()
  }, [loadUsers, loadFormOptions])

  const filteredUsers = useMemo(() => {
    const query = search.trim().toLowerCase()

    return users.filter((item) => {
      const matchesSearch = !query || [
        item.username,
        item.first_name,
        item.last_name,
        item.email,
      ].some((value) => String(value || '').toLowerCase().includes(query))

      const matchesRole =
        roleFilter === 'all' || item.user_type === roleFilter

      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && item.is_active) ||
        (statusFilter === 'inactive' && !item.is_active)

      return matchesSearch && matchesRole && matchesStatus
    })
  }, [users, search, roleFilter, statusFilter])

  const activeCount = users.filter((item) => item.is_active).length
  const inactiveCount = users.length - activeCount

  function openCreateForm() {
    setEditingUser(null)
    setForm(emptyForm)
    setError('')
    setNotice('')
    setShowForm(true)
  }

  function openEditForm(item) {
    navigate(`/users/${item.id}/edit`)
  }

  function closeForm() {
    setShowForm(false)
    setEditingUser(null)
    setForm(emptyForm)
  }

  function handleChange(event) {
    const { name, value } = event.target

    setForm((previous) => ({
      ...previous,
      [name]: value,
      ...(name === 'program' ? { batch: '' } : {}),
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')

    const payload = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      phone_number: form.phone_number.trim() || null,
    }

    try {
      if (editingUser) {
        await updateUser(editingUser.id, payload)
        setNotice('User details updated successfully.')
      } else {
        payload.email = form.email.trim()
        payload.password = form.password
        payload.user_type = form.user_type

        if (form.user_type === 'student') {
          payload.program = form.program
          payload.batch = form.batch
          payload.current_semester = form.current_semester
          payload.academic_session = form.academic_session
        }

        if (form.user_type === 'faculty') {
          payload.employee_id = form.employee_id.trim()
          payload.department = form.department
          payload.designation = form.designation.trim()
          payload.specialization = form.specialization.trim()

          if (form.office) {
            payload.office = form.office
          }
        }

        if (form.user_type === 'staff') {
          payload.employee_id = form.employee_id.trim()
          payload.office = form.office
          payload.designation = form.designation.trim()
        }

        await createAdminUser(payload)
        setNotice('User and role profile created successfully.')
      }

      closeForm()
      await loadUsers()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function toggleUserStatus(item) {
    const action = item.is_active ? 'deactivate' : 'activate'
    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${item.username}?`
    )

    if (!confirmed) return

    setError('')
    setNotice('')

    try {
      await updateUser(item.id, { is_active: !item.is_active })
      setNotice(`User ${action}d successfully.`)
      await loadUsers()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function sendPasswordReset(item) {
    const confirmed = window.confirm(
      `Send a password reset link to ${item.email}? The user will choose a new password.`
    )
    if (!confirmed) return

    setError('')
    setNotice('')
    setResetSendingId(item.id)
    try {
      const result = await sendAdminPasswordReset(item.id)
      setNotice(result.detail || 'Password reset link sent.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setResetSendingId(null)
    }
  }

  async function openUserProfile(item) {
    setProfileUser(item)
    setProfileDetails(null)
    setProfileError('')
    setProfileLoading(true)
    try {
      const details = await fetchAdminUserProfile(item.id)
      setProfileDetails(details)
    } catch (err) {
      setProfileError(getErrorMessage(err))
    } finally {
      setProfileLoading(false)
    }
  }

  function openPasswordReset(item) {
    setPasswordResetUser(item)
    setPasswordResetForm({ newPassword: '', confirmPassword: '' })
    setError('')
  }

  async function handlePasswordResetSubmit(event) {
    event.preventDefault()
    if (!passwordResetUser) return
    setError('')
    setNotice('')
    if (passwordResetForm.newPassword !== passwordResetForm.confirmPassword) {
      setError('The passwords do not match.')
      return
    }

    setPasswordResetSaving(true)
    try {
      const result = await setAdminUserPassword(passwordResetUser.id, passwordResetForm)
      setNotice(result.detail || 'Password reset successfully.')
      const resetOwnAccount = String(passwordResetUser.id) === String(user?.id)
      setPasswordResetUser(null)
      setPasswordResetForm({ newPassword: '', confirmPassword: '' })
      if (resetOwnAccount) {
        signOut()
        navigate('/login', { replace: true })
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setPasswordResetSaving(false)
    }
  }

  if (user?.user_type !== 'admin') {
    return (
      <DashboardLayout role="admin">
        <div className="application-page user-management-page">
          <div className="panel">
            <h2>Access restricted</h2>
            <p>Only administrators can manage users.</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout role="admin">
      <div className="application-page user-management-page">
        <div className="page-heading user-management-heading">
          <div>
            <p className="eyebrow">ADMIN CONTROL PANEL</p>
            <h1>User Management</h1>
            <p>Manage university accounts, roles and account status.</p>
          </div>

          <button className="primary-button" onClick={openCreateForm}>
            + Add New User
          </button>
        </div>

        <div className="metric-grid three user-metrics">
          <div className="metric-card">
            <span>Total Users</span>
            <strong>{users.length}</strong>
          </div>
          <div className="metric-card">
            <span>Active Accounts</span>
            <strong>{activeCount}</strong>
          </div>
          <div className="metric-card">
            <span>Inactive Accounts</span>
            <strong>{inactiveCount}</strong>
          </div>
        </div>

        {notice && <div className="notice">{notice}</div>}
        {error && <div className="form-error">{error}</div>}

        {showForm && (
          <section className="panel">
            <div className="panel-header">
              <h2>{editingUser ? 'Edit User' : 'Create New User'}</h2>
              <button className="plain-button" type="button" onClick={closeForm}>
                Close
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-grid user-form-grid">
                <label>
                  Email Address *
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    required
                    readOnly={Boolean(editingUser)}
                    aria-readonly={Boolean(editingUser)}
                  />
                  {editingUser && <small className="muted-note">University email is fixed for this account.</small>}
                </label>

                <label>
                  First Name *
                  <input
                    name="first_name"
                    value={form.first_name}
                    onChange={handleChange}
                    required
                  />
                </label>

                <label>
                  Last Name *
                  <input
                    name="last_name"
                    value={form.last_name}
                    onChange={handleChange}
                    required
                  />
                </label>

                <label>
                  User Role *
                  <select
                    name="user_type"
                    value={form.user_type}
                    onChange={handleChange}
                    required
                    disabled={Boolean(editingUser)}
                  >
                    <option value="student">Student</option>
                    <option value="faculty">Faculty / Teacher</option>
                    <option value="staff">Staff</option>
                    <option value="external_examiner">External Examiner</option>
                    {editingUser?.user_type === 'admin' && <option value="admin">Central Admin (existing)</option>}
                  </select>
                </label>

                <label>
                  Phone Number
                  <input
                    name="phone_number"
                    value={form.phone_number}
                    onChange={handleChange}
                    placeholder="Optional"
                  />
                </label>

                {!editingUser && (
                  <label className="full-field">
                    Initial Password *
                    <input
                      type="password"
                      name="password"
                      value={form.password}
                      onChange={handleChange}
                      minLength={8}
                      required
                      autoComplete="new-password"
                      placeholder="Minimum 8 characters"
                    />
                  </label>
                )}

                {!editingUser && form.user_type === 'student' && (
                  <>
                    <div className="full-field">
                      <h3>Student Academic Information</h3>
                      <p>Registration number will be generated automatically.</p>
                    </div>

                    <label>
                      Program *
                      <select name="program" value={form.program} onChange={handleChange} required>
                        <option value="">Select Program</option>
                        {formOptions.programs.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name} ({item.code})
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Batch *
                      <select name="batch" value={form.batch} onChange={handleChange} required disabled={!form.program}>
                        <option value="">Select Batch</option>
                        {formOptions.batches
                          .filter((item) => String(item.program) === String(form.program))
                          .map((item) => (
                            <option key={item.id} value={item.id}>{item.name}</option>
                          ))}
                      </select>
                    </label>

                    <label>
                      Current Semester *
                      <select name="current_semester" value={form.current_semester} onChange={handleChange} required>
                        <option value="">Select Semester</option>
                        {formOptions.semesters.map((item) => (
                          <option key={item.id} value={item.id}>{item.title}</option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Academic Session *
                      <select name="academic_session" value={form.academic_session} onChange={handleChange} required>
                        <option value="">Select Academic Session</option>
                        {formOptions.academicSessions.map((item) => (
                          <option key={item.id} value={item.id}>{item.title}</option>
                        ))}
                      </select>
                    </label>
                  </>
                )}

                {!editingUser && form.user_type === 'faculty' && (
                  <>
                    <div className="full-field">
                      <h3>Faculty Information</h3>
                    </div>

                    <label>
                      Employee ID *
                      <input name="employee_id" value={form.employee_id} onChange={handleChange} required />
                    </label>

                    <label>
                      Department *
                      <select name="department" value={form.department} onChange={handleChange} required>
                        <option value="">Select Department</option>
                        {formOptions.departments.map((item) => (
                          <option key={item.id} value={item.id}>{item.name}</option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Designation *
                      <input name="designation" value={form.designation} onChange={handleChange} placeholder="e.g. Lecturer, Assistant Professor" required />
                    </label>

                    <label>
                      Specialization
                      <input name="specialization" value={form.specialization} onChange={handleChange} placeholder="Optional" />
                    </label>

                    <label>
                      Office
                      <select name="office" value={form.office} onChange={handleChange}>
                        <option value="">Select Office (Optional)</option>
                        {formOptions.offices.map((item) => (
                          <option key={item.id} value={item.id}>{item.name}</option>
                        ))}
                      </select>
                    </label>
                  </>
                )}

                {!editingUser && form.user_type === 'staff' && (
                  <>
                    <div className="full-field">
                      <h3>Staff Information</h3>
                    </div>

                    <label>
                      Employee ID *
                      <input name="employee_id" value={form.employee_id} onChange={handleChange} required />
                    </label>

                    <label>
                      Office *
                      <select name="office" value={form.office} onChange={handleChange} required>
                        <option value="">Select Office</option>
                        {formOptions.offices.map((item) => (
                          <option key={item.id} value={item.id}>{item.name}</option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Designation *
                      <input name="designation" value={form.designation} onChange={handleChange} placeholder="e.g. Exam Officer, Fee Officer" required />
                    </label>
                  </>
                )}
              </div>

              <div className="form-actions user-form-actions">
                <button className="primary-button" type="submit" disabled={saving}>
                  {saving ? 'Saving...' : editingUser ? 'Save Changes' : 'Create User'}
                </button>
                <button className="secondary-button" type="button" onClick={closeForm}>
                  Cancel
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>All User Accounts</h2>
              <p>{filteredUsers.length} account(s) found</p>
            </div>
          </div>

          <div className="filter-row user-filter-row">
            <input
              className="search-box"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search name, username or email..."
            />

            <select
              value={roleFilter}
              onChange={(event) => setRoleFilter(event.target.value)}
            >
              <option value="all">All Roles</option>
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
              <option value="staff">Staff</option>
              <option value="external_examiner">External Examiner</option>
              <option value="admin">Admin</option>
            </select>

            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {loading ? (
            <div className="empty-state user-empty-state">Loading users...</div>
          ) : filteredUsers.length === 0 ? (
            <div className="empty-state user-empty-state">No user accounts found.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table user-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((item) => (
                    <tr key={item.id}>
                      <td>{`${item.first_name || ''} ${item.last_name || ''}`.trim() || '—'}</td>
                      <td>{item.username}</td>
                      <td>{item.email}</td>
                      <td>{item.user_type === 'admin' ? 'Central Admin' : String(item.user_type || '').replaceAll('_', ' ')}</td>
                      <td>
                        <span className={`status-chip ${item.is_active ? 'approved' : 'rejected'}`}>
                          {item.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <div className="form-actions user-form-actions">
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={() => openEditForm(item)}
                          >
                            Edit
                          </button>
                          <button
                            className="plain-button"
                            type="button"
                            onClick={() => openUserProfile(item)}
                          >
                            View profile
                          </button>
                          <button
                            className="plain-button"
                            type="button"
                            onClick={() => openPasswordReset(item)}
                          >
                            Reset password
                          </button>
                          <button
                            className="plain-button"
                            type="button"
                            disabled={resetSendingId === item.id}
                            onClick={() => sendPasswordReset(item)}
                          >
                            {resetSendingId === item.id ? 'Sending…' : 'Send reset link'}
                          </button>
                          {item.user_type !== 'admin' && (
                            <button
                              className="plain-button"
                              type="button"
                              onClick={() => toggleUserStatus(item)}
                            >
                              {item.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {profileUser && (
          <div className="profile-modal-backdrop" role="presentation" onMouseDown={(event) => {
            if (event.target === event.currentTarget) setProfileUser(null)
          }}>
            <section className="panel profile-modal" role="dialog" aria-modal="true" aria-labelledby="admin-profile-title">
              <div className="panel-header">
                <div><h2 id="admin-profile-title">User profile</h2><p>{profileUser.username}</p></div>
                <button className="plain-button" type="button" onClick={() => setProfileUser(null)}>Close</button>
              </div>
              {profileLoading ? <div className="empty-state">Loading profile…</div> : profileError ?
                <div className="form-error" role="alert">{profileError}</div> : profileDetails && <div className="admin-profile-details">
                  {profileDetails.profile_picture ?
                    <img className="admin-profile-image" src={mediaUrl(profileDetails.profile_picture)} alt="Saved user profile" /> :
                    <div className="admin-profile-image admin-profile-fallback" aria-label="No profile picture">
                      {(profileDetails.first_name?.[0] || (profileDetails.user_type === 'admin' ? 'A' : profileDetails.username?.[0]) || 'U').toUpperCase()}
                    </div>}
                  <div className="admin-profile-fields">
                    <div><small>Name</small><strong>{[profileDetails.first_name, profileDetails.last_name].filter(Boolean).join(' ') || (profileDetails.user_type === 'admin' ? 'Admin' : '—')}</strong></div>
                    <div><small>Email</small><strong>{profileDetails.email}</strong></div>
                    <div><small>Role</small><strong>{String(profileDetails.user_type || '').replaceAll('_', ' ')}</strong></div>
                    <div><small>Phone</small><strong>{profileDetails.phone_number || '—'}</strong></div>
                    {profileDetails.user_type === 'student' && Object.entries(profileDetails.role_profile || {}).map(([key, value]) => (
                      <div key={key}><small>{key.replaceAll('_', ' ')}</small><strong>{value === false ? 'No' : value || '—'}</strong></div>
                    ))}
                    {(profileDetails.user_type === 'faculty' || profileDetails.user_type === 'staff') && Object.entries(profileDetails.role_profile || {}).map(([key, value]) => (
                      <div key={key}><small>{key.replaceAll('_', ' ')}</small><strong>{value === false ? 'No' : value || '—'}</strong></div>
                    ))}
                    {(profileDetails.user_type === 'faculty' || profileDetails.user_type === 'staff') && <>
                      {profileDetails.user_type === 'faculty' && <div><small>Joining date</small><strong>—</strong></div>}
                    </>}
                    <div className="admin-profile-responsibilities">
                      <small>Current responsibilities</small>
                      {(profileDetails.responsibilities || []).length ? profileDetails.responsibilities.map((responsibility, index) => <strong key={`${responsibility.type}-${index}`}>
                        {responsibility.label}{responsibility.scope ? ` · ${responsibility.scope}` : ''}
                      </strong>) : <strong>—</strong>}
                    </div>
                  </div>
                </div>}
            </section>
          </div>
        )}

        {passwordResetUser && (
          <div className="profile-modal-backdrop" role="presentation">
            <section className="panel password-reset-modal" role="dialog" aria-modal="true" aria-labelledby="admin-reset-title">
              <div className="panel-header">
                <div><h2 id="admin-reset-title">Set a new password</h2><p>For {passwordResetUser.username}</p></div>
                <button className="plain-button" type="button" onClick={() => setPasswordResetUser(null)}>Close</button>
              </div>
              <form className="form-grid admin-password-form" onSubmit={handlePasswordResetSubmit}>
                <label>New password<input type="password" autoComplete="new-password" value={passwordResetForm.newPassword} onChange={(event) => setPasswordResetForm((previous) => ({ ...previous, newPassword: event.target.value }))} required /></label>
                <label>Confirm new password<input type="password" autoComplete="new-password" value={passwordResetForm.confirmPassword} onChange={(event) => setPasswordResetForm((previous) => ({ ...previous, confirmPassword: event.target.value }))} required /></label>
                {error && <div className="full-field form-error" role="alert">{error}</div>}
                <p className="full-field muted-note">The password is validated and securely hashed by the server. It is never shown after submission.</p>
                <div className="full-field form-actions">
                  <button className="primary-button" type="submit" disabled={passwordResetSaving}>{passwordResetSaving ? 'Saving…' : 'Set password'}</button>
                  <button className="secondary-button" type="button" onClick={() => setPasswordResetUser(null)}>Cancel</button>
                </div>
              </form>
            </section>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

export default UserManagement
