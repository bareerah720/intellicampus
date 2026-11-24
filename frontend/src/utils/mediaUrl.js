const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin

export function mediaUrl(path) {
  if (!path) return ''
  try {
    return new URL(path, apiBaseUrl).toString()
  } catch {
    return path
  }
}
