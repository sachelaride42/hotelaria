import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './Perfil.css'

const TIPO_LABEL = { GERENTE: 'Administrador / Gerente', RECEPCIONISTA: 'Recepcionista' }

function Perfil() {
  const [usuario, setUsuario] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    apiFetch('/auth/me')
      .then(setUsuario)
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate])

  return (
    <div className="perfil-page">
      <h1 className="perfil-title">Perfil</h1>

      {loading && (
        <div className="perfil-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando perfil…</p>
        </div>
      )}

      {error && (
        <div className="perfil-feedback perfil-feedback--error" role="alert">
          <p>Não foi possível carregar o perfil.</p>
          <p className="perfil-error-detail">{error}</p>
        </div>
      )}

      {usuario && (
        <div className="perfil-card">
          <div className="perfil-avatar" aria-hidden="true">
            {usuario.nome.charAt(0).toUpperCase()}
          </div>
          <dl className="perfil-campos">
            <div className="perfil-campo">
              <dt className="perfil-campo__label">Nome</dt>
              <dd className="perfil-campo__valor">{usuario.nome}</dd>
            </div>
            <div className="perfil-campo">
              <dt className="perfil-campo__label">E-mail</dt>
              <dd className="perfil-campo__valor">{usuario.email}</dd>
            </div>
            <div className="perfil-campo">
              <dt className="perfil-campo__label">Tipo de usuário</dt>
              <dd className="perfil-campo__valor">
                <span className={`perfil-tipo perfil-tipo--${usuario.tipo.toLowerCase()}`}>
                  {TIPO_LABEL[usuario.tipo] ?? usuario.tipo}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  )
}

export default Perfil
