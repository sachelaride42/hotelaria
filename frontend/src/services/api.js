const BASE_URL = 'http://localhost:8000'

export function getUserRole() {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    return JSON.parse(atob(token.split('.')[1])).role ?? null
  } catch {
    return null
  }
}

function getHeaders() {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    const err = new Error(data.detail || `Erro ${res.status}`)
    err.status = res.status
    throw err
  }
  if (res.status === 204) return null
  return res.json()
}
