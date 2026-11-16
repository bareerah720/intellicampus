
import { apiClient } from './apiClient'

// Fetch application types, dynamic fields and dropdown options
export async function fetchApplicationSetup() {
    const [typesResponse, fieldsResponse, optionsResponse] = await Promise.all([
    apiClient.get('/api/applications/types/'),
    apiClient.get('/api/applications/fields/'),
    apiClient.get('/api/applications/field-options/'),
])
const types = typesResponse.data.filter((type) => type.is_active)

const fields = fieldsResponse.data
const options = optionsResponse.data
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