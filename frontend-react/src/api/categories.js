import { apiFetch } from './client'

export const getRules = (token) =>
  apiFetch('GET', '/api/categories/rules', { token })

export const addKeyword = (token, category, keyword) =>
  apiFetch('POST', `/api/categories/rules/${encodeURIComponent(category)}/keywords`, {
    token,
    body: { keyword },
  })

export const deleteKeyword = (token, category, keyword) =>
  apiFetch('DELETE', `/api/categories/rules/${encodeURIComponent(category)}/keywords/${encodeURIComponent(keyword)}`, { token })
