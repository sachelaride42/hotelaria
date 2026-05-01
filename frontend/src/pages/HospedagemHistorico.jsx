import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './HospedagemHistorico.css'

const FORMA_LABEL = {
  DINHEIRO: 'Dinheiro',
  CARTAO_CREDITO: 'Cartão de Crédito',
  CARTAO_DEBITO: 'Cartão de Débito',
  PIX: 'PIX',
  BOLETO: 'Boleto',
}

function fmtDataHora(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function buildTimeline(hospedagem, pagamentos, consumos) {
  const eventos = []

  eventos.push({
    tipo: 'checkin',
    data: new Date(hospedagem.data_checkin),
    titulo: 'Check-in realizado',
    detalhe: null,
  })

  for (const c of consumos) {
    eventos.push({
      tipo: 'consumo',
      data: new Date(c.data_registro),
      titulo: `${c.descricao}`,
      detalhe: `${c.quantidade}× ${formatBRL(c.valor_unitario)} = ${formatBRL(c.subtotal)}`,
    })
  }

  for (const p of pagamentos) {
    eventos.push({
      tipo: 'pagamento',
      data: new Date(p.data_hora_pagamento),
      titulo: `Pagamento – ${formatBRL(p.valor_pago)}`,
      detalhe: FORMA_LABEL[p.forma_pagamento] ?? p.forma_pagamento,
    })
  }

  return eventos.sort((a, b) => a.data - b.data)
}

export default function HospedagemHistorico() {
  const { hospedagemId } = useParams()
  const navigate = useNavigate()

  const [timeline, setTimeline] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const [hosp, pagamentos, consumos] = await Promise.all([
          apiFetch(`/hospedagens/${hospedagemId}`),
          apiFetch(`/pagamentos/hospedagem/${hospedagemId}`),
          apiFetch(`/itens-consumo/hospedagem/${hospedagemId}`),
        ])
        setTimeline(buildTimeline(hosp, pagamentos, consumos))
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Falha ao carregar o histórico.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [hospedagemId, navigate])

  if (loading) {
    return (
      <div className="hhist-feedback" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p>Carregando histórico…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="hhist-feedback hhist-feedback--error" role="alert">
        <p>{error}</p>
        <button className="hhist-btn-link" onClick={() => navigate(-1)}>← Voltar</button>
      </div>
    )
  }

  return (
    <div className="hhist-page">
      <Link className="hhist-voltar" to={`/hospedagem/${hospedagemId}`}>← Voltar</Link>

      <h1>Histórico</h1>

      {timeline.length === 0 ? (
        <p className="hhist-vazio">Nenhum evento registrado.</p>
      ) : (
        <ol className="hhist-timeline" aria-label="Linha do tempo da hospedagem">
          {timeline.map((ev, i) => (
            <li key={i} className={`hhist-evento hhist-evento--${ev.tipo}`}>
              <div className="hhist-ponto" aria-hidden="true" />
              <div className="hhist-conteudo">
                <span className="hhist-data">{fmtDataHora(ev.data)}</span>
                <span className="hhist-titulo">{ev.titulo}</span>
                {ev.detalhe && <span className="hhist-detalhe">{ev.detalhe}</span>}
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
