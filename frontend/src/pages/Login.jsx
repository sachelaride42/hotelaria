import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'

const BASE_URL = 'http://localhost:8000'

function Login() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setErro('')
    setCarregando(true)

    try {
      const body = new URLSearchParams({ username: email, password: senha })
      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      })

      const data = await res.json()

      if (!res.ok) {
        setErro(data.detail || 'E-mail ou senha incorretos.')
        return
      }

      localStorage.setItem('token', data.access_token)
      navigate('/')
    } catch {
      setErro('Não foi possível conectar ao servidor.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <header className="login-card__header">
          <p className="login-card__brand">HOTEL</p>
          <h1 className="login-card__title">Acesso ao sistema</h1>
          <p className="login-card__subtitle">Entre com suas credenciais para continuar</p>
        </header>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="email" className="form-label">E-mail</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="seu@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              required
              aria-describedby={erro ? 'login-erro' : undefined}
            />
          </div>

          <div className="form-field">
            <label htmlFor="senha" className="form-label">Senha</label>
            <input
              id="senha"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={senha}
              onChange={e => setSenha(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {erro && (
            <p id="login-erro" className="login-error" role="alert">
              {erro}
            </p>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={carregando || !email || !senha}
          >
            {carregando ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
