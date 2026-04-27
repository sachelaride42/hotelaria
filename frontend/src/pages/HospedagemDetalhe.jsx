import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './HospedagemDetalhe.css'

function fmtData(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR')
}

function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const STATUS_LABEL = { ATIVA: 'Ativa', FINALIZADA: 'Finalizada', CANCELADA: 'Cancelada' }
const STATUS_CLASS = { ATIVA: 'badge--ativa', FINALIZADA: 'badge--finalizada', CANCELADA: 'badge--cancelada' }

function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

export default function HospedagemDetalhe() {
  const { hospedagemId } = useParams()
  const navigate = useNavigate()

  const [hospedagem, setHospedagem] = useState(null)
  const [quarto, setQuarto] = useState(null)
  const [tipo, setTipo] = useState(null)
  const [cliente, setCliente] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const hosp = await apiFetch(`/hospedagens/${hospedagemId}`)
        const [q, tipos, clientes] = await Promise.all([
          apiFetch(`/quartos/${hosp.quarto_id}`),
          apiFetch('/tipos-quarto/'),
          apiFetch('/clientes/'),
        ])
        const cli = clientes.find(c => c.id === hosp.cliente_id) ?? null
        setHospedagem(hosp)
        setQuarto(q)
        setTipo(tipos.find(t => t.id === q.tipo_quarto_id) ?? null)
        setCliente(cli)
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Erro ao carregar hospedagem.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [hospedagemId, navigate])

  if (loading) {
    return (
      <div className="page-feedback" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p>Carregando hospedagem…</p>
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

  const diariaNegociada = hospedagem.valor_diaria_negociado
    ? formatBRL(hospedagem.valor_diaria_negociado)
    : null

  return (
    <div className="hospedagem-detalhe">
      <button className="btn-voltar" onClick={() => navigate(-1)}>← Voltar</button>

      <h1>Hospedagem</h1>

      <div className="detalhe-cards">
        <section className="detalhe-card" aria-labelledby="det-title">
          <h2 id="det-title">Detalhes da Hospedagem</h2>
          <dl className="info-list">
            <InfoRow
              label="Quarto"
              value={quarto ? `${quarto.numero}${cliente ? ` – ${cliente.nome}` : ''}` : '—'}
            />
            {tipo && <InfoRow label="Tipo" value={tipo.nome} />}
            <InfoRow
              label="Status"
              value={
                <span className={`badge ${STATUS_CLASS[hospedagem.status]}`}>
                  {STATUS_LABEL[hospedagem.status]}
                </span>
              }
            />
            <InfoRow label="Check-in" value={fmtData(hospedagem.data_checkin)} />
            <InfoRow label="Saída prevista" value={fmtData(hospedagem.data_checkout_previsto)} />
            {hospedagem.data_checkout_real && (
              <InfoRow label="Checkout realizado" value={fmtData(hospedagem.data_checkout_real)} />
            )}
          </dl>
        </section>

        <section className="detalhe-card" aria-labelledby="val-title">
          <h2 id="val-title">Valores</h2>
          <dl className="info-list">
            {tipo && <InfoRow label="Diária base" value={formatBRL(tipo.precoBaseDiaria)} />}
            <InfoRow
              label="Diária negociada"
              value={diariaNegociada ?? <span className="text-muted">—</span>}
            />
            {Number(hospedagem.valor_total) > 0 && (
              <InfoRow label="Total cobrado" value={formatBRL(hospedagem.valor_total)} />
            )}
          </dl>
        </section>
      </div>

      <nav className="hospedagem-nav" aria-label="Seções da hospedagem">
        <Link
          className="nav-link"
          to={`/hospedagem/${hospedagemId}/extrato`}
        >
          Extrato da Conta
        </Link>
        <button
          className="nav-link nav-link--disabled"
          disabled
          title="Em breve"
          aria-disabled="true"
        >
          Hóspedes
        </button>
        <button
          className="nav-link nav-link--disabled"
          disabled
          title="Em breve"
          aria-disabled="true"
        >
          Histórico
        </button>
      </nav>

      {hospedagem.status === 'ATIVA' && (
        <div className="checkout-area">
          <button
            className="btn-checkout"
            onClick={() => navigate(`/checkout/${hospedagemId}`)}
          >
            Fazer Checkout
          </button>
        </div>
      )}
    </div>
  )
}
