const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function apiFetch(method, path, { token, body, params, formData } = {}) {
  const url = new URL(BASE + path)
  if (params) {
    Object.entries(params).forEach(([k, v]) => v != null && v !== '' && url.searchParams.set(k, v))
  }

  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (body) headers['Content-Type'] = 'application/json'

  const res = await fetch(url, {
    method,
    headers,
    body: formData ? formData : body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    localStorage.removeItem('hfc_token')
    localStorage.removeItem('hfc_username')
    window.location.href = '/'
    throw new Error('Session expired')
  }

  if (res.status === 204) return null
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
