const BASE_URL = 'http://localhost:8000'
// const BASE_URL = 'http://192.168.68.106:8000'
export default BASE_URL

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

function friendlyMessage(status, detail) {
  if (detail) return detail
  if (status === 400 || status === 422) return 'Dados inválidos. Verifique as informações e tente novamente.'
  if (status === 403) return 'Você não tem permissão para realizar esta ação.'
  if (status === 404) return 'Registro não encontrado.'
  if (status === 409) return 'Conflito de dados. Recarregue a página e tente novamente.'
  if (status >= 500)  return 'Erro interno do servidor. Tente novamente em instantes.'
  return 'Falha na comunicação com o servidor. Tente novamente.'
}

export async function apiFetch(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { ...getHeaders(), ...options.headers },
    })
  } catch {
    const err = new Error('Falha na comunicação com o servidor. Verifique sua conexão e tente novamente.')
    err.status = 0
    throw err
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    const detail = typeof data.detail === 'string' ? data.detail : null
    const err = new Error(friendlyMessage(res.status, detail))
    err.status = res.status
    throw err
  }
  if (res.status === 204) return null
  return res.json()
}
