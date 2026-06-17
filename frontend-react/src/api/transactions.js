import { apiFetch } from './client'

export const getProcessed = (token, params) =>
  apiFetch('GET', '/api/transactions/processed', { token, params })

export const getPending = (token, params) =>
  apiFetch('GET', '/api/transactions/pending', { token, params })

export const updateTransaction = (token, id, body) =>
  apiFetch('PATCH', `/api/transactions/${id}`, { token, body })

export const approveTransaction = (token, id) =>
  apiFetch('POST', `/api/transactions/${id}/approve`, { token })

export const rejectTransaction = (token, id) =>
  apiFetch('POST', `/api/transactions/${id}/reject`, { token })

export const getDocument = (token, id) =>
  apiFetch('GET', `/api/transactions/${id}/document`, { token })

export const setTags = (token, id, tags) =>
  apiFetch('PUT', `/api/transactions/${id}/tags`, { token, body: { tags } })

export const pollEmail = (token) =>
  apiFetch('POST', '/api/transactions/poll_email', { token })

export const exportCsv = (token, params) => {
  const url = new URL((import.meta.env.VITE_API_BASE ?? 'http://localhost:8000') + '/api/transactions/export')
  if (params) Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v))
  url.searchParams.set('token', token)
  window.open(url.toString())
}
