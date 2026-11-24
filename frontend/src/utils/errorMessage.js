// DRF errors: {field: ["msg"]}, {non_field_errors: [...]}, ya {detail: "msg"}
function flatten(data) {
  if (typeof data === 'string') return [data]
  if (Array.isArray(data)) return data.flatMap(flatten)
  if (data && typeof data === 'object') return Object.values(data).flatMap(flatten)
  return []
}

export function getErrorMessage(error) {
  if (!error.response) {
    if (error.code === 'ECONNABORTED') {
      return 'The server took too long to respond. Please try again.'
    }
    return 'Cannot reach the server. Please check your connection and try again.'
  }

  const { status, data } = error.response

  if (status === 400 || status === 401) {
    const messages = flatten(data)
    if (messages.length > 0) return messages.join(' ')
    return status === 401 ? 'Invalid credentials or expired session.' : 'Please check the entered details.'
  }
  if (status === 403) return 'You do not have permission to perform this action.'
  if (status === 429) return 'Too many attempts. Please wait and try again.'
  if (status === 404) return 'The requested resource was not found.'
  if (status === 409) return 'This record conflicts with an existing one.'
  if (status >= 500) return 'Something went wrong on the server. Please try again later.'

  return 'An unexpected error occurred. Please try again.'
}