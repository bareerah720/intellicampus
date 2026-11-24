
import { apiClient } from './apiClient'

// Fetch application types, dynamic fields and dropdown options
export async function fetchApplicationSetup() {
    const [typesResponse, fieldsResponse, optionsResponse] = await Promise.all([
    apiClient.get('/api/applications/types/'),
    apiClient.get('/api/applications/fields/'),
    apiClient.get('/api/applications/field-options/'),
])
const rows = (value) => Array.isArray(value) ? value : value?.results || []
const types = rows(typesResponse.data).filter((type) => type.is_active)

const fields = rows(fieldsResponse.data)
const options = rows(optionsResponse.data)
return types.map((type) => ({
    ...type,
    fields: fields
    .filter((field) => field.application_type === type.id)
    .map((field) => ({
        ...field,
        options: options.filter((option) => option.field === field.id),
    }))
    .sort((a, b) => a.display_order - b.display_order),
}))
}

// Fetch logged-in student's applications
export async function fetchMyApplications() {
    const response = await apiClient.get('/api/applications/')
    return response.data
}

// Submit a new application
export async function submitApplication(applicationData) {
    const response = await apiClient.post(
    '/api/applications/',
    applicationData)
    return response.data
}


// Fetch applications assigned to the logged-in officer
export async function fetchOfficerInbox() {
  const response = await apiClient.get('/api/applications/inbox/')
  return response.data
}

// Perform an application review action
export async function reviewApplication(id, action, remarks = '') {
  const response = await apiClient.post(
    `/api/applications/${id}/action/`,
    {
      action,
      remarks,
    }
  )

  return response.data
}

// Resubmit a revised application
export async function resubmitApplication(id, applicationData) {
  const response = await apiClient.post(
    `/api/applications/${id}/resubmit/`,
    applicationData
  )

  return response.data
}

// Fetch application tracking details and approval history
export async function fetchApplicationTracking(id) {
  const response = await apiClient.get(
    `/api/applications/${id}/tracking/`
  )

  return response.data
}

export async function fetchApplicationAttachments(applicationId) {
  const response = await apiClient.get('/api/applications/attachments/', {
    params: { application: applicationId },
  })
  return response.data
}

export async function uploadApplicationAttachment(applicationId, file) {
  const formData = new FormData()
  formData.append('application', applicationId)
  formData.append('file_name', file.name)
  formData.append('file_path', file)

  const response = await apiClient.post(
    '/api/applications/attachments/',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return response.data
}

export async function fetchApplicationComments(applicationId) {
  const response = await apiClient.get('/api/applications/comments/', {
    params: { application: applicationId },
  })
  return response.data
}

export async function createApplicationComment(applicationId, comment) {
  const response = await apiClient.post('/api/applications/comments/', {
    application: applicationId,
    comment,
  })
  return response.data
}

export async function fetchApplicationFields() {
  const response = await apiClient.get('/api/applications/fields/')
  return response.data
}

export async function createApplicationField(data) {
  const response = await apiClient.post('/api/applications/fields/', data)
  return response.data
}

export async function updateApplicationField(id, data) {
  const response = await apiClient.patch(`/api/applications/fields/${id}/`, data)
  return response.data
}

export async function deleteApplicationField(id) {
  const response = await apiClient.delete(`/api/applications/fields/${id}/`)
  return response.data
}

export async function fetchApplicationFieldOptions() {
  const response = await apiClient.get('/api/applications/field-options/')
  return response.data
}

export async function createApplicationFieldOption(data) {
  const response = await apiClient.post('/api/applications/field-options/', data)
  return response.data
}

export async function updateApplicationFieldOption(id, data) {
  const response = await apiClient.patch(`/api/applications/field-options/${id}/`, data)
  return response.data
}

export async function deleteApplicationFieldOption(id) {
  const response = await apiClient.delete(`/api/applications/field-options/${id}/`)
  return response.data
}

 // Fetch all applications (Admin only)
export async function fetchAllApplications() {
  const response = await apiClient.get('/api/applications/')
  return response.data
}


// ================================
// ADMIN WORKFLOW MANAGEMENT APIs
// ================================

// Offices
export async function fetchOffices() {
  const response = await apiClient.get('/api/accounts/offices/')
  return response.data
}

// Application Types
export async function fetchAllApplicationTypes() {
  const response = await apiClient.get('/api/applications/types/')
  return response.data
}

export async function createApplicationType(data) {
  const response = await apiClient.post('/api/applications/types/', data)
  return response.data
}

export async function updateApplicationType(id, data) {
  const response = await apiClient.patch(`/api/applications/types/${id}/`, data)
  return response.data
}

export async function deleteApplicationType(id) {
  const response = await apiClient.delete(`/api/applications/types/${id}/`)
  return response.data
}

// Workflows
export async function fetchWorkflows() {
  const response = await apiClient.get('/api/applications/workflows/')
  return response.data
}

export async function createWorkflow(data) {
  const response = await apiClient.post('/api/applications/workflows/', data)
  return response.data
}

export async function updateWorkflow(id, data) {
  const response = await apiClient.patch(`/api/applications/workflows/${id}/`, data)
  return response.data
}

export async function deleteWorkflow(id) {
  const response = await apiClient.delete(`/api/applications/workflows/${id}/`)
  return response.data
}

// Workflow Steps
export async function fetchWorkflowSteps() {
  const response = await apiClient.get('/api/applications/workflow-steps/')
  return response.data
}

export async function createWorkflowStep(data) {
  const response = await apiClient.post('/api/applications/workflow-steps/', data)
  return response.data
}

export async function updateWorkflowStep(id, data) {
  const response = await apiClient.patch(`/api/applications/workflow-steps/${id}/`, data)
  return response.data
}

export async function deleteWorkflowStep(id) {
  const response = await apiClient.delete(`/api/applications/workflow-steps/${id}/`)
  return response.data
}
