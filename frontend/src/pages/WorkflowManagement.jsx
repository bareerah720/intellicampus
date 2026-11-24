import { useCallback, useEffect, useMemo, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { useAuth } from '../hooks/useAuth'
import {
  fetchOffices,
  fetchAllApplicationTypes,
  createApplicationType,
  updateApplicationType,
  fetchWorkflows,
  createWorkflow,
  updateWorkflow,
  fetchWorkflowSteps,
  createWorkflowStep,
  updateWorkflowStep,
  deleteWorkflowStep,
  fetchApplicationFields,
  createApplicationField,
  updateApplicationField,
  deleteApplicationField,
  fetchApplicationFieldOptions,
  createApplicationFieldOption,
  updateApplicationFieldOption,
  deleteApplicationFieldOption,
} from '../services/applicationService'
import {
  fetchResponsibilities,
  createResponsibility,
  updateResponsibility,
  fetchDepartments,
  fetchBatches,
  fetchFacultyProfiles,
  fetchStaffProfiles,
} from '../services/accountsService'

const RESPONSIBILITIES = [
  ['advisor', 'Advisor'],
  ['hod', 'Head of Department'],
  ['fyp_coordinator', 'FYP Coordinator'],
  ['scholarship_coordinator', 'Scholarship Coordinator'],
  ['internship_coordinator', 'Internship Coordinator'],
  ['exam_officer', 'Examination Officer'],
  ['finance_officer', 'Finance Officer'],
  ['student_affairs_officer', 'Student Affairs Officer'],
]

const emptyType = { name: '', description: '', office: '', is_active: true }
const emptyWorkflow = { application_type: '', workflow_name: '', description: '', is_active: true }
const emptyStep = {
  workflow: '',
  office: '',
  step_name: '',
  step_order: 1,
  required_responsibility: '',
  can_approve: true,
  can_reject: true,
  can_request_revision: true,
}
const emptyResponsibility = {
  person_type: 'faculty',
  faculty: '',
  staff: '',
  department: '',
  office: '',
  batch: '',
  responsibility_type: 'advisor',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
  is_active: true,
}
const emptyField = {
  application_type: '',
  label: '',
  field_name: '',
  field_type: 'text',
  placeholder: '',
  is_required: false,
  display_order: 0,
}
const FIELD_TYPES = [
  ['text', 'Text'], ['textarea', 'Long text'], ['number', 'Number'],
  ['email', 'Email'], ['date', 'Date'], ['dropdown', 'Dropdown'],
  ['radio', 'Radio'], ['checkbox', 'Checkbox'], ['file', 'File upload'],
]

function WorkflowManagement() {
  const { user } = useAuth()
  const [tab, setTab] = useState('types')
  const [types, setTypes] = useState([])
  const [workflows, setWorkflows] = useState([])
  const [steps, setSteps] = useState([])
  const [offices, setOffices] = useState([])
  const [responsibilities, setResponsibilities] = useState([])
  const [applicationFields, setApplicationFields] = useState([])
  const [fieldOptions, setFieldOptions] = useState([])
  const [departments, setDepartments] = useState([])
  const [batches, setBatches] = useState([])
  const [facultyProfiles, setFacultyProfiles] = useState([])
  const [staffProfiles, setStaffProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [typeForm, setTypeForm] = useState(emptyType)
  const [editingType, setEditingType] = useState(null)

  const [workflowForm, setWorkflowForm] = useState(emptyWorkflow)
  const [editingWorkflow, setEditingWorkflow] = useState(null)

  const [stepForm, setStepForm] = useState(emptyStep)
  const [editingStep, setEditingStep] = useState(null)
  const [responsibilityForm, setResponsibilityForm] = useState(emptyResponsibility)
  const [editingResponsibility, setEditingResponsibility] = useState(null)
  const [fieldForm, setFieldForm] = useState(emptyField)
  const [fieldOptionsText, setFieldOptionsText] = useState('')
  const [editingField, setEditingField] = useState(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [typeData, workflowData, stepData, officeData, responsibilityData, departmentData, batchData, facultyData, staffData, fieldsData, optionsData] = await Promise.all([
        fetchAllApplicationTypes(),
        fetchWorkflows(),
        fetchWorkflowSteps(),
        fetchOffices(),
        fetchResponsibilities(),
        fetchDepartments(),
        fetchBatches(),
        fetchFacultyProfiles(),
        fetchStaffProfiles(),
        fetchApplicationFields(),
        fetchApplicationFieldOptions(),
      ])
      const rows = (value) => Array.isArray(value) ? value : value?.results || []
      setTypes(rows(typeData))
      setWorkflows(rows(workflowData))
      setSteps(rows(stepData))
      setOffices(rows(officeData))
      setResponsibilities(rows(responsibilityData))
      setApplicationFields(rows(fieldsData))
      setFieldOptions(rows(optionsData))
      setDepartments(rows(departmentData))
      setBatches(rows(batchData))
      setFacultyProfiles(rows(facultyData))
      setStaffProfiles(rows(staffData))
    } catch (err) {
      console.error('Workflow management load error:', err)
      setError(err.response?.data?.detail || 'Unable to load workflow configuration. Please check your access and backend server.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const activeOffices = useMemo(
    () => offices.filter((office) => office.is_active),
    [offices]
  )

  const activeTypes = useMemo(
    () => types.filter((type) => type.is_active),
    [types]
  )

  const activeWorkflows = useMemo(
    () => workflows.filter((workflow) => workflow.is_active),
    [workflows]
  )

  function resetForms() {
    setTypeForm(emptyType)
    setEditingType(null)
    setWorkflowForm(emptyWorkflow)
    setEditingWorkflow(null)
    setStepForm(emptyStep)
    setEditingStep(null)
    setResponsibilityForm(emptyResponsibility)
    setEditingResponsibility(null)
    setFieldForm(emptyField)
    setFieldOptionsText('')
    setEditingField(null)
  }

  async function saveResponsibility(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const data = {
        faculty: responsibilityForm.person_type === 'faculty' ? Number(responsibilityForm.faculty) : null,
        staff: responsibilityForm.person_type === 'staff' ? Number(responsibilityForm.staff) : null,
        department: responsibilityForm.department ? Number(responsibilityForm.department) : null,
        office: responsibilityForm.office ? Number(responsibilityForm.office) : null,
        batch: responsibilityForm.batch ? Number(responsibilityForm.batch) : null,
        responsibility_type: responsibilityForm.responsibility_type,
        start_date: responsibilityForm.start_date,
        end_date: responsibilityForm.end_date || null,
        is_active: responsibilityForm.is_active,
      }
      if (editingResponsibility) {
        await updateResponsibility(editingResponsibility, data)
        setNotice('Responsibility assignment updated.')
      } else {
        await createResponsibility(data)
        setNotice('Responsibility assignment created.')
      }
      setResponsibilityForm(emptyResponsibility)
      setEditingResponsibility(null)
      await loadData()
    } catch (err) {
      setError(typeof err.response?.data === 'object'
        ? JSON.stringify(err.response.data)
        : 'Unable to save responsibility assignment.')
    } finally {
      setSaving(false)
    }
  }

  function editResponsibility(assignment) {
    const personType = assignment.faculty ? 'faculty' : 'staff'
    setEditingResponsibility(assignment.id)
    setResponsibilityForm({
      person_type: personType,
      faculty: String(assignment.faculty || ''),
      staff: String(assignment.staff || ''),
      department: String(assignment.department || ''),
      office: String(assignment.office || ''),
      batch: String(assignment.batch || ''),
      responsibility_type: assignment.responsibility_type,
      start_date: assignment.start_date,
      end_date: assignment.end_date || '',
      is_active: assignment.is_active,
    })
    setTab('responsibilities')
  }

  async function toggleResponsibility(assignment) {
    try {
      await updateResponsibility(assignment.id, { is_active: !assignment.is_active })
      setNotice(`Assignment ${assignment.is_active ? 'deactivated' : 'activated'}.`)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update assignment.')
    }
  }

  async function saveField(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const data = {
        ...fieldForm,
        application_type: Number(fieldForm.application_type),
        display_order: Number(fieldForm.display_order),
      }
      const savedField = editingField
        ? await updateApplicationField(editingField, data)
        : await createApplicationField(data)
      const desiredOptions = ['dropdown', 'radio', 'checkbox'].includes(data.field_type)
        ? fieldOptionsText.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
          const [label, value] = line.split('|').map((part) => part.trim())
          return { label, value: value || label }
        })
        : []
      const existingOptions = fieldOptions.filter((option) => option.field === savedField.id)
      for (const option of existingOptions) {
        if (!desiredOptions.some((item) => item.value === option.value)) {
          await deleteApplicationFieldOption(option.id)
        }
      }
      for (const option of desiredOptions) {
        const existing = existingOptions.find((item) => item.value === option.value)
        if (!existing) {
          await createApplicationFieldOption({ field: savedField.id, ...option })
        } else if (existing.label !== option.label) {
          await updateApplicationFieldOption(existing.id, option)
        }
      }
      setFieldForm(emptyField)
      setFieldOptionsText('')
      setEditingField(null)
      setNotice('Application field saved.')
      await loadData()
    } catch (err) {
      setError(typeof err.response?.data === 'object'
        ? JSON.stringify(err.response.data)
        : 'Unable to save application field.')
    } finally {
      setSaving(false)
    }
  }

  function editField(field) {
    setEditingField(field.id)
    setFieldForm({
      application_type: String(field.application_type),
      label: field.label,
      field_name: field.field_name,
      field_type: field.field_type,
      placeholder: field.placeholder || '',
      is_required: field.is_required,
      display_order: field.display_order,
    })
    setFieldOptionsText(fieldOptions
      .filter((option) => option.field === field.id)
      .map((option) => `${option.label}|${option.value}`)
      .join('\n'))
    setTab('fields')
  }

  async function removeField(field) {
    if (!window.confirm(`Delete the ${field.label} field and its configured options?`)) return
    try {
      await deleteApplicationField(field.id)
      setNotice('Application field deleted.')
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to delete this field.')
    }
  }

  async function removeStep(step) {
    if (!window.confirm(`Delete workflow step ${step.step_name}?`)) return
    try {
      await deleteWorkflowStep(step.id)
      setNotice('Workflow step deleted.')
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to delete this step. It may be referenced by application history.')
    }
  }

  async function saveType(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const data = { ...typeForm, office: Number(typeForm.office) }
      if (editingType) {
        await updateApplicationType(editingType, data)
        setNotice('Application type updated successfully.')
      } else {
        await createApplicationType(data)
        setNotice('Application type created successfully.')
      }
      setTypeForm(emptyType)
      setEditingType(null)
      await loadData()
    } catch (err) {
      const details = err.response?.data
      setError(typeof details === 'object' ? JSON.stringify(details) : 'Unable to save application type.')
    } finally {
      setSaving(false)
    }
  }

  async function saveWorkflow(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const data = {
        ...workflowForm,
        application_type: Number(workflowForm.application_type),
      }
      if (editingWorkflow) {
        await updateWorkflow(editingWorkflow, data)
        setNotice('Workflow updated successfully.')
      } else {
        await createWorkflow(data)
        setNotice('Workflow created successfully.')
      }
      setWorkflowForm(emptyWorkflow)
      setEditingWorkflow(null)
      await loadData()
    } catch (err) {
      const details = err.response?.data
      setError(typeof details === 'object' ? JSON.stringify(details) : 'Unable to save workflow.')
    } finally {
      setSaving(false)
    }
  }

  async function saveStep(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const data = {
        ...stepForm,
        workflow: Number(stepForm.workflow),
        office: Number(stepForm.office),
        step_order: Number(stepForm.step_order),
        required_responsibility: stepForm.required_responsibility || null,
      }
      if (editingStep) {
        await updateWorkflowStep(editingStep, data)
        setNotice('Approval step updated successfully.')
      } else {
        await createWorkflowStep(data)
        setNotice('Approval step created successfully.')
      }
      setStepForm(emptyStep)
      setEditingStep(null)
      await loadData()
    } catch (err) {
      const details = err.response?.data
      setError(typeof details === 'object' ? JSON.stringify(details) : 'Unable to save approval step. Check that step order is unique within its workflow.')
    } finally {
      setSaving(false)
    }
  }

  function editType(type) {
    setEditingType(type.id)
    setTypeForm({
      name: type.name || '',
      description: type.description || '',
      office: String(type.office || ''),
      is_active: type.is_active,
    })
    setTab('types')
  }

  function editWorkflow(workflow) {
    setEditingWorkflow(workflow.id)
    setWorkflowForm({
      application_type: String(workflow.application_type || ''),
      workflow_name: workflow.workflow_name || '',
      description: workflow.description || '',
      is_active: workflow.is_active,
    })
    setTab('workflows')
  }

  function editStep(step) {
    setEditingStep(step.id)
    setStepForm({
      workflow: String(step.workflow || ''),
      office: String(step.office || ''),
      step_name: step.step_name || '',
      step_order: step.step_order || 1,
      required_responsibility: step.required_responsibility || '',
      can_approve: step.can_approve,
      can_reject: step.can_reject,
      can_request_revision: step.can_request_revision,
    })
    setTab('steps')
  }

  async function toggleType(type) {
    setError('')
    setNotice('')
    try {
      await updateApplicationType(type.id, { is_active: !type.is_active })
      setNotice(`Application type ${type.is_active ? 'deactivated' : 'activated'}.`)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update application type.')
    }
  }

  async function toggleWorkflow(workflow) {
    setError('')
    setNotice('')
    try {
      await updateWorkflow(workflow.id, { is_active: !workflow.is_active })
      setNotice(`Workflow ${workflow.is_active ? 'deactivated' : 'activated'}.`)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update workflow.')
    }
  }

  if (user?.user_type !== 'admin') {
    return (
      <DashboardLayout role={user?.user_type || 'student'}>
        <div className="application-page">
          <div className="form-error">You are not authorized to manage workflows.</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout role="admin">
      <div className="application-page">
        <div className="page-heading">
          <div>
            <div className="eyebrow">ADMINISTRATION</div>
            <h1>Workflow Management</h1>
            <p>Configure application categories, approval workflows and responsible offices.</p>
          </div>
          <button className="secondary-button" onClick={loadData} disabled={loading}>
            ↻ Refresh data
          </button>
        </div>

        <div className="metric-grid three">
          <div className="metric-card">
            <span>Application Types</span>
            <strong>{types.length}</strong>
            <small>{activeTypes.length} active</small>
          </div>
          <div className="metric-card">
            <span>Workflows</span>
            <strong>{workflows.length}</strong>
            <small>{activeWorkflows.length} active</small>
          </div>
          <div className="metric-card">
            <span>Approval Steps</span>
            <strong>{steps.length}</strong>
            <small>Configured stages</small>
          </div>
        </div>

        {error && <div className="form-error" style={{ marginBottom: 16 }}>{error}</div>}
        {notice && <div className="notice"><span>✓</span>{notice}<button onClick={() => setNotice('')}>×</button></div>}

        <div className="panel">
          <div className="panel-header" style={{ flexWrap: 'wrap' }}>
            <div>
              <h2>Configuration Sections</h2>
              <p>Choose what you want to configure.</p>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className={tab === 'types' ? 'primary-button' : 'secondary-button'} onClick={() => { resetForms(); setTab('types') }}>Application Types</button>
              <button className={tab === 'workflows' ? 'primary-button' : 'secondary-button'} onClick={() => { resetForms(); setTab('workflows') }}>Workflows</button>
              <button className={tab === 'steps' ? 'primary-button' : 'secondary-button'} onClick={() => { resetForms(); setTab('steps') }}>Approval Steps</button>
              <button className={tab === 'fields' ? 'primary-button' : 'secondary-button'} onClick={() => { resetForms(); setTab('fields') }}>Dynamic Fields</button>
              <button className={tab === 'responsibilities' ? 'primary-button' : 'secondary-button'} onClick={() => { resetForms(); setTab('responsibilities') }}>Responsibilities</button>
            </div>
          </div>

          {loading ? (
            <div className="empty-state"><p>Loading configuration from backend...</p></div>
          ) : (
            <>
              {tab === 'types' && (
                <>
                  <form className="form-grid" onSubmit={saveType}>
                    <label>
                      Application Type Name
                      <input required maxLength={100} value={typeForm.name} onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })} placeholder="e.g. Medical Emergency" />
                    </label>
                    <label>
                      Responsible Office
                      <select required value={typeForm.office} onChange={(e) => setTypeForm({ ...typeForm, office: e.target.value })}>
                        <option value="">Select office</option>
                        {activeOffices.map((office) => <option key={office.id} value={office.id}>{office.name}{office.department_name ? ` — ${office.department_name}` : ''}</option>)}
                      </select>
                    </label>
                    <label className="full-field">
                      Description
                      <textarea rows={3} value={typeForm.description} onChange={(e) => setTypeForm({ ...typeForm, description: e.target.value })} placeholder="Explain when students should use this application type." />
                    </label>
                    <label className="full-field checkbox-row">
                      <span>Active and available to students</span>
                      <input type="checkbox" checked={typeForm.is_active} onChange={(e) => setTypeForm({ ...typeForm, is_active: e.target.checked })} />
                    </label>
                    <div className="form-actions full-field">
                      <button className="primary-button" type="submit" disabled={saving || !activeOffices.length}>{saving ? 'Saving...' : editingType ? 'Update Application Type' : '＋ Add Application Type'}</button>
                      {editingType && <button className="secondary-button" type="button" onClick={() => { setTypeForm(emptyType); setEditingType(null) }}>Cancel edit</button>}
                    </div>
                  </form>

                  <div className="table-scroll" style={{ marginTop: 25 }}>
                    <table className="data-table">
                      <thead><tr><th>Name</th><th>Office</th><th>Status</th><th>Actions</th></tr></thead>
                      <tbody>
                        {types.map((type) => (
                          <tr key={type.id}>
                            <td><strong>{type.name}</strong><small>{type.description || 'No description'}</small></td>
                            <td>{type.office_name || offices.find((o) => o.id === type.office)?.name || '—'}</td>
                            <td><span className={`status-chip ${type.is_active ? 'approved' : 'rejected'}`}>{type.is_active ? 'Active' : 'Inactive'}</span></td>
                            <td>
                              <button className="secondary-button" onClick={() => editType(type)}>Edit</button>{' '}
                              <button className="plain-button" onClick={() => toggleType(type)}>{type.is_active ? 'Deactivate' : 'Activate'}</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!types.length && <div className="empty-state"><p>No application types found.</p></div>}
                  </div>
                </>
              )}

              {tab === 'workflows' && (
                <>
                  <form className="form-grid" onSubmit={saveWorkflow}>
                    <label>
                      Application Type
                      <select required value={workflowForm.application_type} onChange={(e) => setWorkflowForm({ ...workflowForm, application_type: e.target.value })}>
                        <option value="">Select application type</option>
                        {activeTypes.map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}
                      </select>
                    </label>
                    <label>
                      Workflow Name
                      <input required maxLength={100} value={workflowForm.workflow_name} onChange={(e) => setWorkflowForm({ ...workflowForm, workflow_name: e.target.value })} placeholder="e.g. Medical Request Approval" />
                    </label>
                    <label className="full-field">
                      Description
                      <textarea rows={3} value={workflowForm.description} onChange={(e) => setWorkflowForm({ ...workflowForm, description: e.target.value })} placeholder="Describe the approval process." />
                    </label>
                    <label className="full-field checkbox-row">
                      <span>Active workflow</span>
                      <input type="checkbox" checked={workflowForm.is_active} onChange={(e) => setWorkflowForm({ ...workflowForm, is_active: e.target.checked })} />
                    </label>
                    <div className="form-actions full-field">
                      <button className="primary-button" type="submit" disabled={saving || !activeTypes.length}>{saving ? 'Saving...' : editingWorkflow ? 'Update Workflow' : '＋ Add Workflow'}</button>
                      {editingWorkflow && <button className="secondary-button" type="button" onClick={() => { setWorkflowForm(emptyWorkflow); setEditingWorkflow(null) }}>Cancel edit</button>}
                    </div>
                  </form>

                  <div className="table-scroll" style={{ marginTop: 25 }}>
                    <table className="data-table">
                      <thead><tr><th>Workflow</th><th>Application Type</th><th>Steps</th><th>Status</th><th>Actions</th></tr></thead>
                      <tbody>
                        {workflows.map((workflow) => (
                          <tr key={workflow.id}>
                            <td><strong>{workflow.workflow_name}</strong><small>{workflow.description || 'No description'}</small></td>
                            <td>{workflow.application_type_name || types.find((t) => t.id === workflow.application_type)?.name || '—'}</td>
                            <td>{steps.filter((step) => step.workflow === workflow.id).length}</td>
                            <td><span className={`status-chip ${workflow.is_active ? 'approved' : 'rejected'}`}>{workflow.is_active ? 'Active' : 'Inactive'}</span></td>
                            <td>
                              <button className="secondary-button" onClick={() => editWorkflow(workflow)}>Edit</button>{' '}
                              <button className="plain-button" onClick={() => toggleWorkflow(workflow)}>{workflow.is_active ? 'Deactivate' : 'Activate'}</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!workflows.length && <div className="empty-state"><p>No workflows found.</p></div>}
                  </div>
                </>
              )}

              {tab === 'steps' && (
                <>
                  <form className="form-grid" onSubmit={saveStep}>
                    <label>
                      Workflow
                      <select required value={stepForm.workflow} onChange={(e) => setStepForm({ ...stepForm, workflow: e.target.value })}>
                        <option value="">Select workflow</option>
                        {activeWorkflows.map((workflow) => <option key={workflow.id} value={workflow.id}>{workflow.workflow_name}</option>)}
                      </select>
                    </label>
                    <label>
                      Step Name
                      <input required maxLength={100} value={stepForm.step_name} onChange={(e) => setStepForm({ ...stepForm, step_name: e.target.value })} placeholder="e.g. HOD Approval" />
                    </label>
                    <label>
                      Step Order
                      <input type="number" min="1" required value={stepForm.step_order} onChange={(e) => setStepForm({ ...stepForm, step_order: e.target.value })} />
                    </label>
                    <label>
                      Responsible Office
                      <select required value={stepForm.office} onChange={(e) => setStepForm({ ...stepForm, office: e.target.value })}>
                        <option value="">Select office</option>
                        {activeOffices.map((office) => <option key={office.id} value={office.id}>{office.name}{office.department_name ? ` — ${office.department_name}` : ''}</option>)}
                      </select>
                    </label>
                    <label>
                      Required Responsibility
                      <select value={stepForm.required_responsibility} onChange={(e) => setStepForm({ ...stepForm, required_responsibility: e.target.value })}>
                        <option value="">Any eligible officer</option>
                        {RESPONSIBILITIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                    </label>
                    <div className="full-field" style={{ display: 'grid', gap: 12, padding: '10px 0' }}>
                      <strong style={{ fontSize: 12 }}>Allowed actions at this step</strong>
                      <label className="checkbox-row">
                        <span>Can approve</span>
                        <input type="checkbox" checked={stepForm.can_approve} onChange={(e) => setStepForm({ ...stepForm, can_approve: e.target.checked })} />
                      </label>
                      <label className="checkbox-row">
                        <span>Can reject</span>
                        <input type="checkbox" checked={stepForm.can_reject} onChange={(e) => setStepForm({ ...stepForm, can_reject: e.target.checked })} />
                      </label>
                      <label className="checkbox-row">
                        <span>Can request revision</span>
                        <input type="checkbox" checked={stepForm.can_request_revision} onChange={(e) => setStepForm({ ...stepForm, can_request_revision: e.target.checked })} />
                      </label>
                    </div>
                    <div className="form-actions full-field">
                      <button className="primary-button" type="submit" disabled={saving || !activeWorkflows.length || !activeOffices.length}>{saving ? 'Saving...' : editingStep ? 'Update Approval Step' : '＋ Add Approval Step'}</button>
                      {editingStep && <button className="secondary-button" type="button" onClick={() => { setStepForm(emptyStep); setEditingStep(null) }}>Cancel edit</button>}
                    </div>
                  </form>

                  <div className="table-scroll" style={{ marginTop: 25 }}>
                    <table className="data-table">
                      <thead><tr><th>Order</th><th>Step</th><th>Workflow</th><th>Office</th><th>Responsibility</th><th>Actions</th></tr></thead>
                      <tbody>
                        {[...steps].sort((a, b) => a.workflow - b.workflow || a.step_order - b.step_order).map((step) => (
                          <tr key={step.id}>
                            <td>{step.step_order}</td>
                            <td><strong>{step.step_name}</strong></td>
                            <td>{step.workflow_name || workflows.find((w) => w.id === step.workflow)?.workflow_name || '—'}</td>
                            <td>{step.office_name || offices.find((o) => o.id === step.office)?.name || '—'}</td>
                            <td>{RESPONSIBILITIES.find(([value]) => value === step.required_responsibility)?.[1] || 'Any eligible officer'}</td>
                            <td><button className="secondary-button" onClick={() => editStep(step)}>Edit</button>{' '}<button className="plain-button" onClick={() => removeStep(step)}>Delete</button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!steps.length && <div className="empty-state"><p>No approval steps configured.</p></div>}
                  </div>
                </>
              )}

              {tab === 'fields' && (
                <>
                  <form className="form-grid" onSubmit={saveField}>
                    <label>
                      Application type
                      <select required value={fieldForm.application_type} onChange={(event) => setFieldForm({ ...fieldForm, application_type: event.target.value })}>
                        <option value="">Select type</option>
                        {types.map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}
                      </select>
                    </label>
                    <label>
                      Field label
                      <input required maxLength={100} value={fieldForm.label} onChange={(event) => setFieldForm({ ...fieldForm, label: event.target.value })} />
                    </label>
                    <label>
                      Field key
                      <input required maxLength={100} pattern="[A-Za-z][A-Za-z0-9_]*" value={fieldForm.field_name} onChange={(event) => setFieldForm({ ...fieldForm, field_name: event.target.value })} placeholder="example_field" />
                    </label>
                    <label>
                      Field type
                      <select value={fieldForm.field_type} onChange={(event) => setFieldForm({ ...fieldForm, field_type: event.target.value })}>
                        {FIELD_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                    </label>
                    <label>
                      Placeholder
                      <input maxLength={200} value={fieldForm.placeholder} onChange={(event) => setFieldForm({ ...fieldForm, placeholder: event.target.value })} />
                    </label>
                    <label>
                      Display order
                      <input type="number" min="0" value={fieldForm.display_order} onChange={(event) => setFieldForm({ ...fieldForm, display_order: event.target.value })} />
                    </label>
                    {['dropdown', 'radio', 'checkbox'].includes(fieldForm.field_type) && (
                      <label className="full-field">
                        Options (one per line; use Label|value to set a distinct stored value)
                        <textarea rows={4} value={fieldOptionsText} onChange={(event) => setFieldOptionsText(event.target.value)} placeholder={'Undergraduate|undergraduate\nPostgraduate|postgraduate'} required />
                      </label>
                    )}
                    <label className="full-field checkbox-row">
                      <span>Required for students</span>
                      <input type="checkbox" checked={fieldForm.is_required} onChange={(event) => setFieldForm({ ...fieldForm, is_required: event.target.checked })} />
                    </label>
                    <div className="form-actions full-field">
                      <button className="primary-button" type="submit" disabled={saving || !types.length}>{saving ? 'Saving...' : editingField ? 'Update Field' : '＋ Add Field'}</button>
                      {editingField && <button className="secondary-button" type="button" onClick={() => { setFieldForm(emptyField); setFieldOptionsText(''); setEditingField(null) }}>Cancel edit</button>}
                    </div>
                  </form>

                  <div className="table-scroll" style={{ marginTop: 25 }}>
                    <table className="data-table">
                      <thead><tr><th>Field</th><th>Application type</th><th>Input</th><th>Required</th><th>Actions</th></tr></thead>
                      <tbody>
                        {applicationFields.map((field) => (
                          <tr key={field.id}>
                            <td><strong>{field.label}</strong><small>{field.field_name}</small></td>
                            <td>{field.application_type_name || types.find((type) => type.id === field.application_type)?.name || '—'}</td>
                            <td>{FIELD_TYPES.find(([value]) => value === field.field_type)?.[1] || field.field_type}{['dropdown', 'radio', 'checkbox'].includes(field.field_type) && <small>{fieldOptions.filter((option) => option.field === field.id).map((option) => option.label).join(', ')}</small>}</td>
                            <td>{field.is_required ? 'Yes' : 'No'}</td>
                            <td><button className="secondary-button" onClick={() => editField(field)}>Edit</button>{' '}<button className="plain-button" onClick={() => removeField(field)}>Delete</button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!applicationFields.length && <div className="empty-state"><p>No dynamic fields configured.</p></div>}
                  </div>
                </>
              )}

              {tab === 'responsibilities' && (
                <>
                  <form className="form-grid" onSubmit={saveResponsibility}>
                    <label>
                      Assignment holder
                      <select value={responsibilityForm.person_type} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, person_type: event.target.value, faculty: '', staff: '' })}>
                        <option value="faculty">Faculty</option>
                        <option value="staff">Staff</option>
                      </select>
                    </label>
                    {responsibilityForm.person_type === 'faculty' ? (
                      <label>
                        Faculty member
                        <select required value={responsibilityForm.faculty} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, faculty: event.target.value })}>
                          <option value="">Select faculty</option>
                          {facultyProfiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.user_name || profile.employee_id} · {profile.employee_id}</option>)}
                        </select>
                      </label>
                    ) : (
                      <label>
                        Staff member
                        <select required value={responsibilityForm.staff} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, staff: event.target.value })}>
                          <option value="">Select staff member</option>
                          {staffProfiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.user_name || profile.employee_id} · {profile.employee_id}</option>)}
                        </select>
                      </label>
                    )}
                    <label>
                      Responsibility
                      <select required value={responsibilityForm.responsibility_type} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, responsibility_type: event.target.value })}>
                        {RESPONSIBILITIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                    </label>
                    <label>
                      Office
                      <select value={responsibilityForm.office} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, office: event.target.value })}>
                        <option value="">No specific office</option>
                        {offices.map((office) => <option key={office.id} value={office.id}>{office.name}</option>)}
                      </select>
                    </label>
                    <label>
                      Department scope
                      <select value={responsibilityForm.department} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, department: event.target.value })}>
                        <option value="">University-wide</option>
                        {departments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
                      </select>
                    </label>
                    <label>
                      Batch scope (advisor)
                      <select value={responsibilityForm.batch} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, batch: event.target.value })}>
                        <option value="">No batch scope</option>
                        {batches.map((batch) => <option key={batch.id} value={batch.id}>{batch.name} · {batch.program_name}</option>)}
                      </select>
                    </label>
                    <label>
                      Starts on
                      <input type="date" required value={responsibilityForm.start_date} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, start_date: event.target.value })} />
                    </label>
                    <label>
                      Ends on
                      <input type="date" value={responsibilityForm.end_date} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, end_date: event.target.value })} />
                    </label>
                    <label className="full-field checkbox-row">
                      <span>Assignment active</span>
                      <input type="checkbox" checked={responsibilityForm.is_active} onChange={(event) => setResponsibilityForm({ ...responsibilityForm, is_active: event.target.checked })} />
                    </label>
                    <div className="form-actions full-field">
                      <button className="primary-button" type="submit" disabled={saving}>{saving ? 'Saving...' : editingResponsibility ? 'Update Assignment' : '＋ Add Assignment'}</button>
                      {editingResponsibility && <button className="secondary-button" type="button" onClick={() => { setResponsibilityForm(emptyResponsibility); setEditingResponsibility(null) }}>Cancel edit</button>}
                    </div>
                  </form>

                  <div className="table-scroll" style={{ marginTop: 25 }}>
                    <table className="data-table">
                      <thead><tr><th>Person</th><th>Responsibility</th><th>Scope</th><th>Office</th><th>Dates</th><th>Status</th><th>Actions</th></tr></thead>
                      <tbody>
                        {responsibilities.map((assignment) => (
                          <tr key={assignment.id}>
                            <td><strong>{assignment.faculty_name || assignment.staff_name}</strong><small>{assignment.faculty ? 'Faculty' : 'Staff'}</small></td>
                            <td>{RESPONSIBILITIES.find(([value]) => value === assignment.responsibility_type)?.[1] || assignment.responsibility_type}</td>
                            <td>{assignment.department_name || 'University-wide'}{assignment.batch_name ? ` · ${assignment.batch_name}` : ''}</td>
                            <td>{assignment.office_name || '—'}</td>
                            <td>{assignment.start_date}{assignment.end_date ? ` – ${assignment.end_date}` : ' – Open-ended'}</td>
                            <td><span className={`status-chip ${assignment.is_active ? 'approved' : 'rejected'}`}>{assignment.is_active ? 'Active' : 'Inactive'}</span></td>
                            <td><button className="secondary-button" onClick={() => editResponsibility(assignment)}>Edit</button>{' '}<button className="plain-button" onClick={() => toggleResponsibility(assignment)}>{assignment.is_active ? 'Deactivate' : 'Activate'}</button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!responsibilities.length && <div className="empty-state"><p>No responsibility assignments configured.</p></div>}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}

export default WorkflowManagement
