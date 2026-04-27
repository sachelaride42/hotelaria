import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './Dashboard.css'

const OCUPACAO_LABEL = { LIVRE: 'Livre', OCUPADO: 'Ocupado', MANUTENCAO: 'Manutenção' }
const LIMPEZA_LABEL = { LIMPO: 'Limpo', SUJO: 'Sujo' }

function RoomCard({ quarto, tipoNome, onClick, navigating }) {
  const statusClass = `room-card--${quarto.status_ocupacao.toLowerCase()}`
  const limpezaClass = `room-card__limpeza--${quarto.status_limpeza.toLowerCase()}`

  return (
    <button
      className={`room-card ${statusClass}${navigating ? ' room-card--loading' : ''}`}
      aria-label={`Quarto ${quarto.numero} – ${OCUPACAO_LABEL[quarto.status_ocupacao]}. Clique para ver detalhes`}
      onClick={onClick}
      disabled={navigating}
    >
      <div className="room-card__header">
        <span className="room-card__number">{quarto.numero}</span>
        <div className="room-card__header-right">
          <span className="room-card__status-badge">
            {OCUPACAO_LABEL[quarto.status_ocupacao]}
          </span>
          {navigating
            ? <span className="room-card__spinner" aria-hidden="true" />
            : <span className="room-card__arrow" aria-hidden="true">›</span>
          }
        </div>
      </div>
      <dl className="room-card__info">
        <div>
          <dt>Tipo</dt>
          <dd>{tipoNome}</dd>
        </div>
        <div>
          <dt>Andar</dt>
          <dd>{quarto.andar}º</dd>
        </div>
        <div>
          <dt>Limpeza</dt>
          <dd className={limpezaClass}>{LIMPEZA_LABEL[quarto.status_limpeza]}</dd>
        </div>
      </dl>
    </button>
  )
}

function StatusFilter({ value, onChange }) {
  const options = [
    { value: '', label: 'Todos' },
    { value: 'LIVRE', label: 'Livres' },
    { value: 'OCUPADO', label: 'Ocupados' },
    { value: 'MANUTENCAO', label: 'Manutenção' },
  ]
  return (
    <div className="dashboard-filters" role="group" aria-label="Filtrar por status">
      {options.map(opt => (
        <button
          key={opt.value}
          className={`filter-btn${value === opt.value ? ' filter-btn--active' : ''}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function Dashboard() {
  const [quartos, setQuartos] = useState([])
  const [tipos, setTipos] = useState({})
  const [filtro, setFiltro] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [navigatingId, setNavigatingId] = useState(null)
  const navigate = useNavigate()

  async function handleCardClick(quarto) {
    if (navigatingId) return
    setNavigatingId(quarto.id)
    try {
      if (quarto.status_ocupacao === 'OCUPADO') {
        const hospedagens = await apiFetch(`/hospedagens/?quarto_id=${quarto.id}&status=ATIVA`)
        if (hospedagens.length > 0) {
          navigate(`/hospedagem/${hospedagens[0].id}`)
        } else {
          navigate(`/quarto/${quarto.id}`)
        }
      } else {
        navigate(`/quarto/${quarto.id}`)
      }
    } catch {
      setNavigatingId(null)
    }
  }

  useEffect(() => {
    Promise.all([
      apiFetch('/quartos/'),
      apiFetch('/tipos-quarto/').catch(() => []),
    ])
      .then(([quartosData, tiposData]) => {
        setQuartos(quartosData)
        const tiposMap = {}
        tiposData.forEach(t => { tiposMap[t.id] = t.nome })
        setTipos(tiposMap)
      })
      .catch(err => {
        if (err.status === 401) {
          navigate('/login')
        } else {
          setError(err.message)
        }
      })
      .finally(() => setLoading(false))
  }, [navigate])

  const quartosFiltrados = filtro
    ? quartos.filter(q => q.status_ocupacao === filtro)
    : quartos

  const contagens = {
    total: quartos.length,
    livres: quartos.filter(q => q.status_ocupacao === 'LIVRE').length,
    ocupados: quartos.filter(q => q.status_ocupacao === 'OCUPADO').length,
    manutencao: quartos.filter(q => q.status_ocupacao === 'MANUTENCAO').length,
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Dashboard</h1>
        {!loading && !error && (
          <div className="dashboard-stats" aria-label="Resumo dos quartos">
            <span className="stat">
              <strong>{contagens.total}</strong> quartos
            </span>
            <span className="stat stat--livre">
              <strong>{contagens.livres}</strong> livres
            </span>
            <span className="stat stat--ocupado">
              <strong>{contagens.ocupados}</strong> ocupados
            </span>
            {contagens.manutencao > 0 && (
              <span className="stat stat--manutencao">
                <strong>{contagens.manutencao}</strong> manutenção
              </span>
            )}
          </div>
        )}
      </div>

      {!loading && !error && (
        <StatusFilter value={filtro} onChange={setFiltro} />
      )}

      {loading && (
        <div className="dashboard-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando quartos…</p>
        </div>
      )}

      {error && (
        <div className="dashboard-feedback dashboard-feedback--error" role="alert">
          <p>Não foi possível carregar os quartos.</p>
          <p className="error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && quartosFiltrados.length === 0 && (
        <div className="dashboard-feedback" role="status">
          <p>Nenhum quarto encontrado{filtro ? ` com status "${OCUPACAO_LABEL[filtro]}"` : ''}.</p>
        </div>
      )}

      {!loading && !error && quartosFiltrados.length > 0 && (
        <div className="rooms-grid" aria-label="Lista de quartos">
          {quartosFiltrados.map(quarto => (
            <RoomCard
              key={quarto.id}
              quarto={quarto}
              tipoNome={tipos[quarto.tipo_quarto_id] ?? `Tipo ${quarto.tipo_quarto_id}`}
              onClick={() => handleCardClick(quarto)}
              navigating={navigatingId === quarto.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard
