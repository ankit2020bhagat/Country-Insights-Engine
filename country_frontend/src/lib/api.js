// src/lib/api.js
const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  /** POST /query */
  query: (query) =>
    request('/query', { method: 'POST', body: JSON.stringify({ query }) }),

  /** GET /history */
  history: ({ limit = 20, offset = 0, status, country } = {}) => {
    const params = new URLSearchParams({ limit, offset })
    if (status)  params.set('status', status)
    if (country) params.set('country', country)
    return request(`/history?${params}`)
  },

  /** GET /history/:id */
  historyItem: (id) => request(`/history/${id}`),

  /** GET /health */
  health: () => request('/health'),

  /** POST /admin/cache/purge */
  purgCache: () => request('/admin/cache/purge', { method: 'POST' }),
}
