import { apiFetch } from './client'

export const getStatements = (token) =>
  apiFetch('GET', '/api/transactions/statements', { token })

export const uploadDocument = (token, file) => {
  const form = new FormData()
  form.append('file', file)
  return apiFetch('POST', '/api/upload', { token, formData: form })
}
