import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './Checkout.css'

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function fmtData(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

function toDatetimeLocal(date) {
  const pad = n => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

// Replica a lógica do backend (calculadora_diarias.py)
function calcDiariasFlexivel(checkin, checkout, valorDiaria) {
  const ciDay = new Date(new Date(checkin).toDateString())
  const coDay = new Date(checkout.toDateString())
  const dias = Math.max(1, Math.round((coDay - ciDay) / 86400000))
  let total = dias * valorDiaria

  const hora = checkout.getHours() + checkout.getMinutes() / 60
  if (hora > 12) {
    const extra = hora - 12
    if (extra <= 3)      total += valorDiaria * 0.25
    else if (extra <= 6) total += valorDiaria * 0.50
    else                 total += valorDiaria
  }
  return { dias, total: Math.round(total * 100) / 100 }
}

const FORMAS = [
  { value: 'DINHEIRO',       label: 'Dinheiro' },
  { value: 'CARTAO_CREDITO', label: 'Cartão de Crédito' },
  { value: 'CARTAO_DEBITO',  label: 'Cartão de Débito' },
  { value: 'PIX',            label: 'PIX' },
  { value: 'BOLETO',         label: 'Boleto' },
]

const FORMA_LABEL = Object.fromEntries(FORMAS.map(f => [f.value, f.label]))

// ── Component ─────────────────────────────────────────────────────────────────

export default function Checkout() {
  const { hospedagemId } = useParams()
  const navigate = useNavigate()

  // Dados carregados
  const [hospedagem, setHospedagem] = useState(null)
  const [quarto, setQuarto]         = useState(null)
  const [tipo, setTipo]             = useState(null)
  const [itens, setItens]           = useState([])
  const [cliente, setCliente]       = useState(null)
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  // Pagamentos
  const [pagamentos, setPagamentos]       = useState([])
  const [novosPagIds, setNovosPagIds]     = useState([])
  const [formaAtual, setFormaAtual]       = useState('')
  const [valorAtual, setValorAtual]       = useState('')
  const [adicionando, setAdicionando]     = useState(false)
  const [erroPag, setErroPag]             = useState(null)

  // Checkout
  const [checkoutTime, setCheckoutTime]   = useState(new Date())
  const [confirmando, setConfirmando]     = useState(false)
  const [cancelando, setCancelando]       = useState(false)
  const [erroCheckout, setErroCheckout]   = useState(null)

  const surchargeInfo = useRef(null)

  useEffect(() => {
    async function load() {
      try {
        const [hosp, itensData, pags, tipos, clientes] = await Promise.all([
          apiFetch(`/hospedagens/${hospedagemId}`),
          apiFetch(`/itens-consumo/hospedagem/${hospedagemId}`),
          apiFetch(`/pagamentos/hospedagem/${hospedagemId}`),
          apiFetch('/tipos-quarto/'),
          apiFetch('/clientes/'),
        ])
        const q = await apiFetch(`/quartos/${hosp.quarto_id}`)
        setHospedagem(hosp)
        setQuarto(q)
        setTipo(tipos.find(t => t.id === q.tipo_quarto_id) ?? null)
        setItens(itensData)
        setPagamentos(pags)
        setCliente(clientes.find(c => c.id === hosp.cliente_id) ?? null)
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Erro ao carregar dados.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [hospedagemId, navigate])

  // ── Derivados ──────────────────────────────────────────────────────────────

  const valorDiaria = hospedagem
    ? Number(hospedagem.valor_diaria_negociado ?? tipo?.precoBaseDiaria ?? 0)
    : 0

  const diarias = hospedagem && tipo
    ? calcDiariasFlexivel(hospedagem.data_checkin, checkoutTime, valorDiaria)
    : null

  // Calcula surcharge para exibição
  function getSurchargeDesc() {
    const hora = checkoutTime.getHours() + checkoutTime.getMinutes() / 60
    if (hora <= 12) return null
    const extra = hora - 12
    if (extra <= 3) return `+25% (saída entre 12h–15h)`
    if (extra <= 6) return `+50% (saída entre 15h–18h)`
    return `+100% (saída após 18h)`
  }

  const subtotalConsumo = itens.reduce((acc, it) => acc + it.quantidade * it.valor_unitario, 0)
  const totalGeral      = (diarias?.total ?? 0) + subtotalConsumo
  const totalPago       = pagamentos.reduce((acc, p) => acc + Number(p.valor_pago), 0)
  const saldoRestante   = Math.max(0, Math.round((totalGeral - totalPago) * 100) / 100)

  // ── Handlers ───────────────────────────────────────────────────────────────

  function handleCheckoutTimeChange(e) {
    if (e.target.value) setCheckoutTime(new Date(e.target.value))
  }

  async function handleAdicionarPagamento(e) {
    e.preventDefault()
    setErroPag(null)
    const val = parseFloat(valorAtual)
    if (!formaAtual) { setErroPag('Selecione a forma de pagamento.'); return }
    if (!val || val <= 0) { setErroPag('Informe um valor válido.'); return }

    setAdicionando(true)
    try {
      const pag = await apiFetch('/pagamentos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hospedagem_id: Number(hospedagemId),
          valor_pago: Math.round(val * 100) / 100,
          forma_pagamento: formaAtual,
        }),
      })
      setPagamentos(prev => [...prev, pag])
      setNovosPagIds(prev => [...prev, pag.id])
      setFormaAtual('')
      setValorAtual('')
    } catch (err) {
      setErroPag(err.message ?? 'Erro ao registrar pagamento.')
    } finally {
      setAdicionando(false)
    }
  }

  async function handleCancelar() {
    setCancelando(true)
    try {
      await Promise.all(novosPagIds.map(id => apiFetch(`/pagamentos/${id}`, { method: 'DELETE' })))
    } catch {
      // ignora erros de deleção ao cancelar
    }
    navigate(`/hospedagem/${hospedagemId}`)
  }

  async function handleConfirmar() {
    setErroCheckout(null)
    setConfirmando(true)
    try {
      await apiFetch(`/hospedagens/${hospedagemId}/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          versao_quarto: quarto.versao,
          data_checkout_real: toDatetimeLocal(checkoutTime) + ':00',
        }),
      })
      navigate('/', { state: { sucesso: 'Checkout realizado com sucesso!' } })
    } catch (err) {
      setErroCheckout(err.message ?? 'Erro ao realizar checkout.')
      setConfirmando(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="page-feedback" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p>Carregando checkout…</p>
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

  const surchargeDesc = getSurchargeDesc()

  return (
    <div className="checkout-page">
      <button className="btn-voltar" onClick={() => navigate(-1)}>← Voltar</button>

      <h1>Realizar Checkout</h1>
      {quarto && (
        <p className="checkout-subtitle">
          Quarto {quarto.numero}{cliente ? ` – ${cliente.nome}` : ''}
        </p>
      )}

      {/* ── Resumo da Conta ── */}
      <section className="checkout-section" aria-labelledby="resumo-title">
        <h2 id="resumo-title">Resumo da Conta</h2>
        <div className="table-wrapper">
          <table className="checkout-table">
            <colgroup>
              <col style={{ width: '18%' }} />
              <col style={{ width: '9%' }} />
              <col style={{ width: '27%' }} />
              <col style={{ width: '8%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '14%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Data</th>
                <th>Descrição</th>
                <th className="col-num">Qtd</th>
                <th className="col-num">Valor unit.</th>
                <th className="col-num">Total</th>
              </tr>
            </thead>
            <tbody>
              {diarias && (
                <tr className="row-diarias">
                  <td>Diárias</td>
                  <td>{fmtData(hospedagem.data_checkin)}</td>
                  <td>{tipo?.nome ?? 'quarto'}</td>
                  <td className="col-num">{diarias.dias}</td>
                  <td className="col-num">{formatBRL(valorDiaria)}</td>
                  <td className="col-num">{formatBRL(diarias.total)}</td>
                </tr>
              )}
              {itens.map(it => (
                <tr key={it.id}>
                  <td>Produto / Serviço</td>
                  <td>{fmtData(it.data_registro)}</td>
                  <td>{it.descricao}</td>
                  <td className="col-num">{it.quantidade}</td>
                  <td className="col-num">{formatBRL(it.valor_unitario)}</td>
                  <td className="col-num">{formatBRL(it.quantidade * it.valor_unitario)}</td>
                </tr>
              ))}
              {!diarias && itens.length === 0 && (
                <tr>
                  <td colSpan={6} className="table-empty">Nenhum item na conta.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Data/hora de saída ── */}
      <section className="checkout-section" aria-labelledby="saida-title">
        <h2 id="saida-title">Data / Hora de Saída</h2>
        <div className="saida-row">
          <input
            type="datetime-local"
            className="form-input"
            value={toDatetimeLocal(checkoutTime)}
            onChange={handleCheckoutTimeChange}
            aria-label="Data e hora de saída"
          />
          <span className="saida-info">
            {diarias && (
              <>
                {diarias.dias} {diarias.dias === 1 ? 'diária' : 'diárias'}
                {surchargeDesc && <span className="surcharge-badge">{surchargeDesc}</span>}
              </>
            )}
          </span>
        </div>

        <div className="total-geral" aria-live="polite">
          Total Geral: <strong>{formatBRL(totalGeral)}</strong>
        </div>
      </section>

      {/* ── Registrar Pagamento ── */}
      <section className="checkout-section" aria-labelledby="pag-title">
        <h2 id="pag-title">Registrar Pagamento</h2>
        <form className="pag-form" onSubmit={handleAdicionarPagamento} noValidate>
          <div className="pag-form__fields">
            <div className="form-group">
              <label className="form-label" htmlFor="forma-pag">Forma de Pagamento</label>
              <select
                id="forma-pag"
                className="form-input"
                value={formaAtual}
                onChange={e => setFormaAtual(e.target.value)}
                required
              >
                <option value="">Selecione a Forma</option>
                {FORMAS.map(f => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="valor-pag">Valor a Pagar (R$)</label>
              <input
                id="valor-pag"
                className="form-input"
                type="number"
                min="0.01"
                step="0.01"
                placeholder={saldoRestante > 0 ? formatBRL(saldoRestante).replace('R$ ', '') : '0,00'}
                value={valorAtual}
                onChange={e => setValorAtual(e.target.value)}
                required
              />
            </div>
          </div>
          {erroPag && <p className="form-erro" role="alert">{erroPag}</p>}
          <button type="submit" className="btn btn--outline" disabled={adicionando}>
            {adicionando ? 'Adicionando…' : 'Adicionar Pagamento'}
          </button>
        </form>

        {/* Histórico de pagamentos */}
        {pagamentos.length > 0 && (
          <div className="pag-historico">
            <h3>Histórico de Pagamentos</h3>
            <ul className="pag-list">
              {pagamentos.map(p => (
                <li key={p.id} className="pag-item">
                  <span className="pag-item__valor">{formatBRL(p.valor_pago)}</span>
                  <span className="pag-item__forma">– {FORMA_LABEL[p.forma_pagamento] ?? p.forma_pagamento}</span>
                </li>
              ))}
            </ul>

            <dl className="pag-saldo">
              <div className="pag-saldo__row">
                <dt>Total da conta</dt>
                <dd>{formatBRL(totalGeral)}</dd>
              </div>
              <div className="pag-saldo__row">
                <dt>Total pago</dt>
                <dd>{formatBRL(totalPago)}</dd>
              </div>
              <div className={`pag-saldo__row pag-saldo__restante${saldoRestante === 0 ? ' pag-saldo__restante--ok' : ''}`}>
                <dt>Restante</dt>
                <dd><strong>{formatBRL(saldoRestante)}</strong></dd>
              </div>
            </dl>
          </div>
        )}
      </section>

      {/* ── Erros e ações finais ── */}
      {erroCheckout && (
        <p className="form-erro" role="alert">{erroCheckout}</p>
      )}

      {saldoRestante > 0 && pagamentos.length > 0 && (
        <p className="aviso-saldo" role="note">
          Registre o pagamento restante ({formatBRL(saldoRestante)}) para concluir.
        </p>
      )}

      <div className="checkout-actions">
        <button
          className="btn btn--outline"
          onClick={handleCancelar}
          disabled={cancelando || confirmando}
        >
          {cancelando ? 'Cancelando…' : 'Cancelar Checkout'}
        </button>
        <button
          className="btn btn--danger"
          onClick={handleConfirmar}
          disabled={saldoRestante > 0 || confirmando || cancelando}
          title={saldoRestante > 0 ? 'Quite o saldo antes de concluir' : undefined}
        >
          {confirmando ? 'Processando…' : 'Concluir Checkout e Liberar Quarto'}
        </button>
      </div>
    </div>
  )
}
