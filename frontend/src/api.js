const TOKEN_KEY = 'landing_studio_token'
const EMAIL_KEY = 'landing_studio_email'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getEmail() {
  return localStorage.getItem(EMAIL_KEY)
}

export function saveSession({ token, email }) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(EMAIL_KEY, email)
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(EMAIL_KEY)
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    clearSession()
    window.location.href = '/login'
    throw new Error('Session expired')
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const data = await res.json()
      if (data.detail) detail = typeof data.detail === 'string' ? data.detail : detail
    } catch {
      /* keep default */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

export async function downloadZip(genId, businessName) {
  const res = await fetch(`/api/generations/${genId}/download`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  if (!res.ok) throw new Error('Download failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${businessName.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.zip`
  a.click()
  URL.revokeObjectURL(url)
}
