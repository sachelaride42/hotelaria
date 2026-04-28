import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './Extrato.css'

function fmtData(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function calcDiarias(hospedagem, tipo) {
  if (!hospedagem || !tipo) return null
  const entrada = new Date(hospedagem.data_checkin)
  const saida   = new Date(hospedagem.data_checkout_previsto)
  const dias    = Math.max(1, Math.round((saida - entrada) / 86400000))
  const diaria  = Number(hospedagem.valor_diaria_negociado ?? tipo.precoBaseDiaria)
  return { dias, diaria, total: dias * diaria }
}

function ItemRow({ it, ativo, onSaved, onDeleted }) {
  const [editing, setEditing]               = useState(false)
  const [descricao, setDescricao]           = useState(it.descricao)
  const [quantidade, setQtd]                = useState(String(it.quantidade))
  const [valorUnit, setValor]               = useState(String(it.valor_unitario))
  const [salvando, setSalvando]             = useState(false)
  const [excluindo, setExcluindo]           = useState(false)
  const [confirmandoExcluir, setConfirmando] = useState(false)
  const [erro, setErro]                     = useState(null)

  function cancelEdit() {
    setDescricao(it.descricao)
    setQtd(String(it.quantidade))
    setValor(String(it.valor_unitario))
    setErro(null)
    setEditing(false)
  }

  async function handleSave() {
    const qtd = parseInt(quantidade, 10)
    const val = parseFloat(valorUnit)
    if (!descricao.trim() || qtd <= 0 || isNaN(qtd) || val <= 0 || isNaN(val)) {
      setErro('Preencha todos os campos corretamente.')
      return
    }
    setSalvando(true)
    setErro(null)
    try {
      const atualizado = await apiFetch(`/itens-consumo/${it.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ descricao: descricao.trim(), quantidade: qtd, valor_unitario: Math.round(val * 100) / 100 }),
      })
      onSaved(atualizado)
      setEditing(false)
    } catch (err) {
      setErro(err.message ?? 'Erro ao salvar.')
    } finally {
      setSalvando(false)
    }
  }

  async function handleDelete() {
    setExcluindo(true)
    try {
      await apiFetch(`/itens-consumo/${it.id}`, { method: 'DELETE' })
      onDeleted(it.id)
    } catch (err) {
      setErro(err.message ?? 'Erro ao excluir.')
      setExcluindo(false)
      setConfirmando(false)
    }
  }

  const previewVal = parseFloat(valorUnit)
  const previewQtd = parseInt(quantidade, 10)
  const previewOk  = !isNaN(previewVal) && !isNaN(previewQtd) && previewVal > 0 && previewQtd > 0

  if (editing) {
    return (
      <>
        <tr className="row-editing">
          <td>Produto / Serviço</td>
          <td>{fmtData(it.data_registro)}</td>
          <td>
            <input
              className="cell-input"
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              autoFocus
              aria-label="Descrição do item"
            />
          </td>
          <td className="col-num">
            <input
              className="cell-input cell-input--num"
              type="number"
              min="1"
              value={quantidade}
              onChange={e => setQtd(e.target.value)}
              aria-label="Quantidade"
            />
          </td>
          <td className="col-num">
            <input
              className="cell-input cell-input--num"
              type="number"
              min="0.01"
              step="0.01"
              value={valorUnit}
              onChange={e => setValor(e.target.value)}
              aria-label="Valor unitário"
            />
          </td>
          <td className="col-num">
            {previewOk ? formatBRL(previewQtd * previewVal) : '—'}
          </td>
          <td className="col-acoes">
            <div className="extrato-acoes">
              <button
                className="btn-acao"
                onClick={handleSave}
                disabled={salvando}
              >
                {salvando ? 'Salvando…' : 'Salvar'}
              </button>
              <button
                className="btn-acao btn-acao--aviso"
                onClick={cancelEdit}
                disabled={salvando}
              >
                Cancelar
              </button>
            </div>
          </td>
        </tr>
        {erro && (
          <tr className="row-erro">
            <td colSpan={7}>{erro}</td>
          </tr>
        )}
      </>
    )
  }

  return (
    <>
      <tr>
        <td>Produto / Serviço</td>
        <td>{fmtData(it.data_registro)}</td>
        <td>{it.descricao}</td>
        <td className="col-num">{it.quantidade}</td>
        <td className="col-num">{formatBRL(it.valor_unitario)}</td>
        <td className="col-num">{formatBRL(it.quantidade * it.valor_unitario)}</td>
        <td className="col-acoes">
          {ativo && (
            <div className="extrato-acoes">
              {confirmandoExcluir ? (
                <>
                  <span style={{ fontSize: '12px', color: 'var(--text)', whiteSpace: 'nowrap' }}>
                    Excluir item?
                  </span>
                  <button
                    className="btn-acao btn-acao--perigo"
                    onClick={handleDelete}
                    disabled={excluindo}
                  >
                    {excluindo ? 'Excluindo…' : 'Confirmar'}
                  </button>
                  <button
                    className="btn-acao"
                    onClick={() => setConfirmando(false)}
                    disabled={excluindo}
                  >
                    Cancelar
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="btn-acao"
                    onClick={() => setEditing(true)}
                  >
                    Editar
                  </button>
                  <button
                    className="btn-acao btn-acao--perigo"
                    onClick={() => setConfirmando(true)}
                  >
                    Excluir
                  </button>
                </>
              )}
            </div>
          )}
        </td>
      </tr>
      {erro && (
        <tr className="row-erro">
          <td colSpan={7}>{erro}</td>
        </tr>
      )}
    </>
  )
}

export default function Extrato() {
  const { hospedagemId } = useParams()
  const navigate = useNavigate()

  const [hospedagem, setHospedagem] = useState(null)
  const [tipo, setTipo]             = useState(null)
  const [itens, setItens]           = useState([])
  const [catalogo, setCatalogo]     = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  // Painel de lançamento
  const [avulso, setAvulso]         = useState(false)
  const [produtoId, setProdutoId]   = useState('')
  const [nomeAvulso, setNomeAvulso] = useState('')
  const [valorUnit, setValorUnit]   = useState('')
  const [quantidade, setQuantidade] = useState('1')
  const [enviando, setEnviando]     = useState(false)
  const [sucesso, setSucesso]       = useState(false)
  const [erroLanc, setErroLanc]     = useState(null)

  const sucessoTimer = useRef(null)

  useEffect(() => {
    async function load() {
      try {
        const [hosp, itensData, catalogoData, tipos] = await Promise.all([
          apiFetch(`/hospedagens/${hospedagemId}`),
          apiFetch(`/itens-consumo/hospedagem/${hospedagemId}`),
          apiFetch('/catalogo/'),
          apiFetch('/tipos-quarto/'),
        ])
        const quarto = await apiFetch(`/quartos/${hosp.quarto_id}`)
        setHospedagem(hosp)
        setItens(itensData)
        setCatalogo(catalogoData)
        setTipo(tipos.find(t => t.id === quarto.tipo_quarto_id) ?? null)
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Erro ao carregar extrato.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [hospedagemId, navigate])

  function handleProdutoChange(e) {
    const id = e.target.value
    setProdutoId(id)
    if (id) {
      const prod = catalogo.find(p => String(p.id) === id)
      if (prod) setValorUnit(parseFloat(prod.preco_padrao).toFixed(2))
    } else {
      setValorUnit('')
    }
  }

  function handleAvulsoToggle(e) {
    setAvulso(e.target.checked)
    setProdutoId('')
    setNomeAvulso('')
    setValorUnit('')
    setQuantidade('1')
    setErroLanc(null)
  }

  const qtd   = parseInt(quantidade, 10)
  const valor = parseFloat(valorUnit)
  const preview = !isNaN(qtd) && !isNaN(valor) && qtd > 0 && valor > 0
    ? qtd * valor
    : null

  async function handleLancar(e) {
    e.preventDefault()
    setErroLanc(null)

    const descricao = avulso
      ? nomeAvulso.trim()
      : catalogo.find(p => String(p.id) === produtoId)?.descricao ?? ''

    if (!descricao) { setErroLanc('Informe o nome do item.'); return }
    if (!qtd || qtd <= 0) { setErroLanc('Quantidade inválida.'); return }
    if (!valor || valor <= 0) { setErroLanc('Valor unitário inválido.'); return }

    setEnviando(true)
    try {
      await apiFetch('/itens-consumo/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hospedagem_id: Number(hospedagemId),
          descricao,
          quantidade: qtd,
          valor_unitario: Math.round(valor * 100) / 100,
        }),
      })
      const novosItens = await apiFetch(`/itens-consumo/hospedagem/${hospedagemId}`)
      setItens(novosItens)
      setProdutoId('')
      setNomeAvulso('')
      setValorUnit('')
      setQuantidade('1')
      setAvulso(false)
      setSucesso(true)
      clearTimeout(sucessoTimer.current)
      sucessoTimer.current = setTimeout(() => setSucesso(false), 3000)
    } catch (err) {
      setErroLanc(err.message ?? 'Erro ao lançar item.')
    } finally {
      setEnviando(false)
    }
  }

  if (loading) {
    return (
      <div className="page-feedback" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p>Carregando extrato…</p>
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

  const ativo = hospedagem.status === 'ATIVA'
  const diarias = calcDiarias(hospedagem, tipo)
  const subtotalConsumo = itens.reduce((acc, it) => acc + it.quantidade * it.valor_unitario, 0)
  const subtotalTotal   = (diarias?.total ?? 0) + subtotalConsumo

  return (
    <div className="extrato-page">
      <button className="btn-voltar" onClick={() => navigate(-1)}>← Voltar</button>

      <h1>Extrato da Conta</h1>

      <section className="extrato-section" aria-labelledby="hist-title">
        <h2 id="hist-title">Histórico</h2>
        <div className="table-wrapper">
          <table className="extrato-table">
            <colgroup>
              <col style={{ width: '16%' }} />
              <col style={{ width: '9%' }} />
              <col style={{ width: '25%' }} />
              <col style={{ width: '7%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '17%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Data</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Valor unit.</th>
                <th>Total</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {diarias && (
                <tr className="row-diarias">
                  <td>Diárias</td>
                  <td>{fmtData(hospedagem.data_checkin)}</td>
                  <td>{tipo?.nome ?? 'quarto'}</td>
                  <td className="col-num">{diarias.dias}</td>
                  <td className="col-num">{formatBRL(diarias.diaria)}</td>
                  <td className="col-num">{formatBRL(diarias.total)}</td>
                  <td className="col-acoes" />
                </tr>
              )}
              {itens.length === 0 && !diarias && (
                <tr>
                  <td colSpan={7} className="table-empty">Nenhum item lançado.</td>
                </tr>
              )}
              {itens.map(it => (
                <ItemRow
                  key={it.id}
                  it={it}
                  ativo={ativo}
                  onSaved={atualizado =>
                    setItens(prev => prev.map(i => i.id === atualizado.id ? atualizado : i))
                  }
                  onDeleted={id =>
                    setItens(prev => prev.filter(i => i.id !== id))
                  }
                />
              ))}
            </tbody>
          </table>
        </div>
        <p className="subtotal">
          Subtotal: <strong>{formatBRL(subtotalTotal)}</strong>
        </p>
      </section>

      {ativo && (
        <section className="extrato-section lancamento-panel" aria-labelledby="lanc-title">
          <h2 id="lanc-title">Painel de Lançamento</h2>

          <form onSubmit={handleLancar} noValidate>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={avulso}
                onChange={handleAvulsoToggle}
              />
              Item avulso?
            </label>

            {avulso ? (
              <div className="form-group">
                <label className="form-label" htmlFor="nome-avulso">Nome do item</label>
                <input
                  id="nome-avulso"
                  className="form-input"
                  type="text"
                  placeholder="Ex.: Café da manhã"
                  value={nomeAvulso}
                  onChange={e => setNomeAvulso(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label" htmlFor="produto-select">Produto / Serviço</label>
                <select
                  id="produto-select"
                  className="form-input"
                  value={produtoId}
                  onChange={handleProdutoChange}
                  required
                >
                  <option value="">Selecione o Serviço</option>
                  {catalogo.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.descricao}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="valor-unit">Valor unitário (R$)</label>
                <input
                  id="valor-unit"
                  className="form-input"
                  type="number"
                  min="0.01"
                  step="0.01"
                  placeholder="0,00"
                  value={valorUnit}
                  onChange={e => setValorUnit(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="quantidade">Quantidade</label>
                <input
                  id="quantidade"
                  className="form-input"
                  type="number"
                  min="1"
                  step="1"
                  value={quantidade}
                  onChange={e => setQuantidade(e.target.value)}
                  required
                />
              </div>
            </div>

            {preview !== null && (
              <p className="preview-total" aria-live="polite">
                {qtd} × {formatBRL(valor)} = <strong>{formatBRL(preview)}</strong>
              </p>
            )}

            {erroLanc && (
              <p className="erro-lanc" role="alert">{erroLanc}</p>
            )}

            <button
              type="submit"
              className="btn-lancar"
              disabled={enviando || preview === null}
            >
              {enviando ? 'Lançando…' : 'Lançar na Conta'}
            </button>
          </form>

          {sucesso && (
            <div className="sucesso-banner" role="status" aria-live="polite">
              Item lançado com sucesso!
            </div>
          )}
        </section>
      )}
    </div>
  )
}
