import { apiFetch } from './client'

export const getByCategory = (token, params) =>
  apiFetch('GET', '/api/analytics/by_category', { token, params })

export const getTrends = (token, params) =>
  apiFetch('GET', '/api/analytics/trends', { token, params })

export const getByTag = (token, params) =>
  apiFetch('GET', '/api/analytics/by_tag', { token, params })

export const getByMonth = (token, params) =>
  apiFetch('GET', '/api/analytics/by_month', { token, params })

export const getByOwner = (token, params) =>
  apiFetch('GET', '/api/analytics/by_owner', { token, params })

export const getCategoryTrends = (token, params) =>
  apiFetch('GET', '/api/analytics/category_trends', { token, params })
