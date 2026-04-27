import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './QuartoDetalhe.css'

function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const OCUPACAO_LABEL = { LIVRE: 'Livre', OCUPADO: 'Ocupado', MANUTENCAO: 'Manutenção' }
const LIMPEZA_LABEL  = { LIMPO: 'Limpo', SUJO: 'Sujo' }
const OCUPACAO_CLASS = { LIVRE: 'badge--livre', OCUPADO: 'badge--ocupado', MANUTENCAO: 'badge--manutencao' }
const LIMPEZA_CLASS  = { LIMPO: 'limpeza--limpo', SUJO: 'limpeza--sujo' }

function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

export default function QuartoDetalhe() {
  const { quartoId } = useParams()
  const navigate = useNavigate()

  const [quarto, setQuarto] = useState(null)
  const [tipo, setTipo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const [q, tipos] = await Promise.all([
          apiFetch(`/quartos/${quartoId}`),
          apiFetch('/tipos-quarto/'),
        ])
        setQuarto(q)
        setTipo(tipos.find(t => t.id === q.tipo_quarto_id) ?? null)
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Erro ao carregar quarto.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [quartoId, navigate])

  if (loading) {
    return (
      <div className="page-feedback" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p>Carregando quarto…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-feedback page-feedback--error" role="alert">
        <p>{error}</p>
        <button className="btn-link" onClick={() => navigate(-1)}>← Voltar</button>
      </div>
    )
  }

  return (
    <div className="quarto-detalhe">
      <button className="btn-voltar" onClick={() => navigate(-1)}>← Voltar</button>

      <h1>Quarto {quarto.numero}</h1>

      <section className="detalhe-card" aria-labelledby="quarto-title">
        <h2 id="quarto-title">Detalhes do Quarto</h2>
        <dl className="info-list">
          <InfoRow label="Número" value={quarto.numero} />
          <InfoRow label="Andar" value={`${quarto.andar}º`} />
          {tipo && <InfoRow label="Tipo" value={tipo.nome} />}
          {tipo?.capacidade && (
            <InfoRow
              label="Capacidade"
              value={`${tipo.capacidade} ${tipo.capacidade === 1 ? 'pessoa' : 'pessoas'}`}
            />
          )}
          {tipo?.precoBaseDiaria && (
            <InfoRow label="Diária base" value={formatBRL(tipo.precoBaseDiaria)} />
          )}
          <InfoRow
            label="Status"
            value={
              <span className={`badge ${OCUPACAO_CLASS[quarto.status_ocupacao]}`}>
                {OCUPACAO_LABEL[quarto.status_ocupacao]}
              </span>
            }
          />
          <InfoRow
            label="Limpeza"
            value={
              <span className={LIMPEZA_CLASS[quarto.status_limpeza]}>
                {LIMPEZA_LABEL[quarto.status_limpeza]}
              </span>
            }
          />
        </dl>
      </section>

    </div>
  )
}
