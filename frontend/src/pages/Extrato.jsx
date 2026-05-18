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

/* ── COMPONENTE DA LINHA ── */
function ItemRow({ it, ativo, onPedirEdicao, onPedirExclusao }) {
  return (
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
            <button className="btn-acao" onClick={() => onPedirEdicao(it)}>
              Editar
            </button>
            <button className="btn-acao btn-acao--perigo" onClick={() => onPedirExclusao(it)}>
              Excluir
            </button>
          </div>
        )}
      </td>
    </tr>
  )
}

/* ── COMPONENTE PRINCIPAL ── */
export default function Extrato() {
  const { hospedagemId } = useParams()
  const navigate = useNavigate()

  const [hospedagem, setHospedagem] = useState(null)
  const [quarto, setQuarto]         = useState(null)
  const [cliente, setCliente]       = useState(null)
  const [tipo, setTipo]             = useState(null)
  const [itens, setItens]           = useState([])
  const [catalogo, setCatalogo]     = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  // Estados para o modal de exclusão
  const [confirmandoExcluir, setConfirmandoExcluir] = useState(null)
  const [excluindo, setExcluindo]               = useState(false)
  const [erroExcluir, setErroExcluir]           = useState(null)

  // Estados para o modal de edição
  const [editando, setEditando]                 = useState(null) // guarda o objeto completo do item sendo editado
  const [formEdit, setFormEdit]                 = useState({ descricao: '', quantidade: '', valor_unitario: '' })
  const [salvandoEdit, setSalvandoEdit]         = useState(false)
  const [erroEdit, setErroEdit]                 = useState(null)

  // Painel de lançamento (Novos itens)
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
        const [hosp, itensData, catalogoData, tipos, clientes] = await Promise.all([
          apiFetch(`/hospedagens/${hospedagemId}`),
          apiFetch(`/itens-consumo/hospedagem/${hospedagemId}`),
          apiFetch('/catalogo/'),
          apiFetch('/tipos-quarto/'),
          apiFetch('/clientes/'),
        ])
        const q = await apiFetch(`/quartos/${hosp.quarto_id}`)
        setHospedagem(hosp)
        setQuarto(q)
        setCliente(clientes.find(c => c.id === hosp.cliente_id) ?? null)
        setItens(itensData)
        setCatalogo(catalogoData)
        setTipo(tipos.find(t => t.id === q.tipo_quarto_id) ?? null)
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Falha ao carregar o extrato. Recarregue a página.')
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
      setErroLanc(err.message ?? 'Falha ao lançar o item. Tente novamente.')
    } finally {
      setEnviando(false)
    }
  }

  /* ── Ações de Edição (Modal) ── */
  function abrirModalEdicao(item) {
    setEditando(item)
    setFormEdit({
      descricao: item.descricao,
      quantidade: String(item.quantidade),
      valor_unitario: String(item.valor_unitario)
    })
    setErroEdit(null)
  }

  function handleFormEditChange(e) {
    const { name, value } = e.target
    setFormEdit(prev => ({ ...prev, [name]: value }))
  }

  async function executarEdicao(e) {
    e.preventDefault()
    const qEd = parseInt(formEdit.quantidade, 10)
    const vEd = parseFloat(formEdit.valor_unitario)

    if (!formEdit.descricao.trim() || qEd <= 0 || isNaN(qEd) || vEd <= 0 || isNaN(vEd)) {
      setErroEdit('Preencha todos os campos corretamente.')
      return
    }

    setSalvandoEdit(true)
    setErroEdit(null)
    try {
      const atualizado = await apiFetch(`/itens-consumo/${editando.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          descricao: formEdit.descricao.trim(), 
          quantidade: qEd, 
          valor_unitario: Math.round(vEd * 100) / 100 
        }),
      })
      setItens(prev => prev.map(i => i.id === atualizado.id ? atualizado : i))
      setEditando(null)
    } catch (err) {
      setErroEdit(err.message ?? 'Falha ao salvar o item. Tente novamente.')
    } finally {
      setSalvandoEdit(false)
    }
  }

  /* ── Ações de Exclusão (Modal) ── */
  async function executarExclusao() {
    if (!confirmandoExcluir) return
    setExcluindo(true)
    setErroExcluir(null)
    try {
      await apiFetch(`/itens-consumo/${confirmandoExcluir.id}`, { method: 'DELETE' })
      setItens(prev => prev.filter(i => i.id !== confirmandoExcluir.id))
      setConfirmandoExcluir(null)
    } catch (err) {
      setErroExcluir(err.message ?? 'Falha ao excluir o item. Tente novamente.')
    } finally {
      setExcluindo(false)
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

  // Preview dinâmico para o modal de edição
  const previewQtdEdit = parseInt(formEdit.quantidade, 10)
  const previewValEdit = parseFloat(formEdit.valor_unitario)
  const previewTotalEdit = !isNaN(previewQtdEdit) && !isNaN(previewValEdit) && previewQtdEdit > 0 && previewValEdit > 0
    ? previewQtdEdit * previewValEdit
    : null

  return (
    <div className="extrato-page">
      <button className="btn-voltar" onClick={() => navigate(-1)}>← Voltar</button>

      <h1>Extrato da Conta</h1>
      {quarto && (
        <p className="extrato-subtitle">
          Quarto {quarto.numero}{cliente ? ` – ${cliente.nome}` : ''}
        </p>
      )}

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
                  onPedirEdicao={abrirModalEdicao}
                  onPedirExclusao={itemCompleto => setConfirmandoExcluir(itemCompleto)}
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
              <input type="checkbox" checked={avulso} onChange={handleAvulsoToggle} />
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

            <button type="submit" className="btn-lancar" disabled={enviando || preview === null}>
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

      {/* ── MODAL DE EDIÇÃO ── */}
      {editando && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Editar item"
          onClick={e => { if (e.target === e.currentTarget) setEditando(null) }}
        >
          <div className="modal">
            <div className="modal__header">
              <h2 className="modal__titulo">Editar item do extrato</h2>
              <button className="modal__fechar" onClick={() => setEditando(null)} aria-label="Fechar">✕</button>
            </div>
            
            <form onSubmit={executarEdicao} noValidate>
              <div className="modal__corpo" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="edit-descricao">Descrição</label>
                  <input
                    id="edit-descricao"
                    name="descricao"
                    className="form-input"
                    value={formEdit.descricao}
                    onChange={handleFormEditChange}
                    required
                  />
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-valor">Valor Unitário (R$)</label>
                    <input
                      id="edit-valor"
                      name="valor_unitario"
                      type="number"
                      min="0.01"
                      step="0.01"
                      className="form-input"
                      value={formEdit.valor_unitario}
                      onChange={handleFormEditChange}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-quantidade">Quantidade</label>
                    <input
                      id="edit-quantidade"
                      name="quantidade"
                      type="number"
                      min="1"
                      step="1"
                      className="form-input"
                      value={formEdit.quantidade}
                      onChange={handleFormEditChange}
                      required
                    />
                  </div>
                </div>

                {previewTotalEdit !== null && (
                  <p className="preview-total" aria-live="polite" style={{ margin: '4px 0 0' }}>
                    Total estimado: <strong>{formatBRL(previewTotalEdit)}</strong>
                  </p>
                )}

                {erroEdit && (
                  <p className="page-erro" role="alert" style={{ margin: '8px 0 0' }}>{erroEdit}</p>
                )}
              </div>

              <div className="modal__footer">
                <button type="button" className="btn btn--ghost" onClick={() => setEditando(null)} disabled={salvandoEdit}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn--primary" disabled={salvandoEdit}>
                  {salvandoEdit ? 'Salvando…' : 'Salvar alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL DE CONFIRMAÇÃO DE EXCLUSÃO ── */}
      {confirmandoExcluir && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar exclusão"
          onClick={e => { if (e.target === e.currentTarget) { setConfirmandoExcluir(null); setErroExcluir(null) } }}
        >
          <div className="modal modal--pequeno">
            <div className="modal__header">
              <h2 className="modal__titulo">Excluir item do extrato</h2>
              <button className="modal__fechar" onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }} aria-label="Fechar">✕</button>
            </div>
            <p className="modal__corpo">
              Tem certeza que deseja remover o item <strong>{confirmandoExcluir.descricao}</strong> do extrato? Esta ação não pode ser desfeita.
            </p>
            {erroExcluir && (
              <p className="page-erro" role="alert" style={{ margin: '0 24px' }}>{erroExcluir}</p>
            )}
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }}>
                Cancelar
              </button>
              <button className="btn btn--perigo" onClick={executarExclusao} disabled={excluindo}>
                {excluindo ? 'Excluindo…' : 'Confirmar exclusão'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}