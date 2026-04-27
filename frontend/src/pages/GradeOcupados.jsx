import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './GradeOcupados.css'

const LIMPEZA_LABEL = { LIMPO: 'Limpo', SUJO: 'Sujo' }

function OccupiedCard({ quarto, tipoNome, onClick }) {
  const limpezaClass = `ocard__limpeza--${quarto.status_limpeza.toLowerCase()}`

  return (
    <button
      className="ocard"
      aria-label={`Quarto ${quarto.numero} – Ocupado. Clique para ver detalhes`}
      onClick={onClick}
    >
      <div className="ocard__header">
        <span className="ocard__number">{quarto.numero}</span>
        <span className="ocard__arrow" aria-hidden="true">›</span>
      </div>
      <dl className="ocard__info">
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

/**
 * destino: 'hospedagem' | 'checkout'
 * titulo: string
 */
export default function GradeOcupados({ titulo, destino }) {
  const [quartos, setQuartos]           = useState([])
  const [tipos, setTipos]               = useState({})
  const [hospedagemMap, setHospedagemMap] = useState({}) // quartoId → hospedagemId
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      apiFetch('/quartos/?status_ocupacao=OCUPADO'),
      apiFetch('/tipos-quarto/').catch(() => []),
      apiFetch('/hospedagens/?status=ATIVA'),
    ])
      .then(([quartosData, tiposData, hospedagensData]) => {
        setQuartos(quartosData)
        const tiposMap = {}
        tiposData.forEach(t => { tiposMap[t.id] = t.nome })
        setTipos(tiposMap)
        const hMap = {}
        hospedagensData.forEach(h => { hMap[h.quarto_id] = h.id })
        setHospedagemMap(hMap)
      })
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate])

  function handleClick(quarto) {
    const hospedagemId = hospedagemMap[quarto.id]
    if (!hospedagemId) return
    if (destino === 'checkout') {
      navigate(`/checkout/${hospedagemId}`)
    } else if (destino === 'extrato') {
      navigate(`/hospedagem/${hospedagemId}/extrato`)
    } else {
      navigate(`/hospedagem/${hospedagemId}`)
    }
  }

  return (
    <div className="grade-ocupados">
      <div className="grade-header">
        <h1 className="grade-title">{titulo}</h1>
        {!loading && !error && (
          <span className="grade-badge">
            {quartos.length} {quartos.length === 1 ? 'quarto ocupado' : 'quartos ocupados'}
          </span>
        )}
      </div>

      {loading && (
        <div className="grade-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando…</p>
        </div>
      )}

      {error && (
        <div className="grade-feedback grade-feedback--error" role="alert">
          <p>Não foi possível carregar os quartos.</p>
          <p className="grade-error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && quartos.length === 0 && (
        <div className="grade-feedback" role="status">
          <p>Nenhum quarto ocupado no momento.</p>
        </div>
      )}

      {!loading && !error && quartos.length > 0 && (
        <div className="ocard-grid" aria-label={titulo}>
          {quartos.map(quarto => (
            <OccupiedCard
              key={quarto.id}
              quarto={quarto}
              tipoNome={tipos[quarto.tipo_quarto_id] ?? `Tipo ${quarto.tipo_quarto_id}`}
              onClick={() => handleClick(quarto)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
