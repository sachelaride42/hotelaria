import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import './Produtos.css'

const CATEGORIA_LABEL = { PRODUTO: 'Produto', SERVICO: 'Serviço' }
const FORM_INICIAL = { descricao: '', preco_padrao: '', categoria: 'PRODUTO' }

function fmtBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function Produtos() {
  const [itens, setItens]                       = useState([])
  const [filtro, setFiltro]                     = useState('')
  const [loading, setLoading]                   = useState(true)
  const [error, setError]                       = useState(null)
  const [editando, setEditando]                 = useState(null)
  const [form, setForm]                         = useState(FORM_INICIAL)
  const [salvando, setSalvando]                 = useState(false)
  const [erroForm, setErroForm]                 = useState(null)
  const [confirmandoExcluir, setConfirmandoExcluir] = useState(null)
  const [excluindo, setExcluindo]               = useState(false)
  const navigate = useNavigate()

  const role = getUserRole()

  const itensFiltrados = filtro.trim()
    ? itens.filter(i => i.descricao.toLowerCase().includes(filtro.toLowerCase()))
    : itens

  useEffect(() => {
    if (role !== 'GERENTE') return
    apiFetch('/catalogo/')
      .then(setItens)
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate, role])

  function iniciarEdicao(item) {
    setEditando(item)
    setForm({
      descricao: item.descricao,
      preco_padrao: String(item.preco_padrao),
      categoria: item.categoria,
    })
    setErroForm(null)
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  }

  function cancelar() {
    setEditando(null)
    setForm(FORM_INICIAL)
    setErroForm(null)
  }

  function handleForm(e) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  async function salvar(e) {
    e.preventDefault()
    if (!form.descricao.trim() || form.preco_padrao === '' || Number(form.preco_padrao) < 0) {
      setErroForm('Preencha nome e valor unitário.')
      return
    }
    setSalvando(true)
    setErroForm(null)
    const payload = {
      descricao: form.descricao.trim(),
      preco_padrao: Number(form.preco_padrao),
      categoria: form.categoria,
    }
    try {
      if (editando) {
        const atualizado = await apiFetch(`/catalogo/${editando.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
        setItens(prev => prev.map(i => i.id === atualizado.id ? atualizado : i))
      } else {
        const novo = await apiFetch('/catalogo/', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setItens(prev => [...prev, novo])
      }
      cancelar()
    } catch (err) {
      if (err.status === 401) navigate('/login')
      else setErroForm(err.message)
    } finally {
      setSalvando(false)
    }
  }

  async function excluir() {
    if (!confirmandoExcluir) return
    setExcluindo(true)
    try {
      await apiFetch(`/catalogo/${confirmandoExcluir}`, { method: 'DELETE' })
      setItens(prev => prev.filter(i => i.id !== confirmandoExcluir))
      if (editando?.id === confirmandoExcluir) cancelar()
    } catch (err) {
      if (err.status === 401) navigate('/login')
      else setError(err.message)
    } finally {
      setExcluindo(false)
      setConfirmandoExcluir(null)
    }
  }

  if (role !== 'GERENTE') {
    return (
      <div className="pd-page">
        <h1 className="pd-title">Gestão de Produtos / Serviços</h1>
        <p className="pd-restrito">Acesso restrito a administradores.</p>
      </div>
    )
  }

  return (
    <div className="pd-page">
      <h1 className="pd-title">Gestão de Produtos / Serviços</h1>

      {loading && (
        <div className="pd-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando produtos…</p>
        </div>
      )}

      {error && (
        <div className="pd-feedback pd-feedback--error" role="alert">
          <p>Não foi possível carregar os dados.</p>
          <p className="pd-error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Busca */}
          <div className="pd-busca">
            <label className="pd-busca__label" htmlFor="pd-filtro">Buscar Produto / Serviço</label>
            <div className="pd-busca__row">
              <input
                id="pd-filtro"
                className="form-input pd-busca__input"
                placeholder="Pesquisar pelo nome…"
                value={filtro}
                onChange={e => setFiltro(e.target.value)}
              />
            </div>
          </div>

          {/* Tabela */}
          <div className="table-wrapper">
            <table className="pd-table" aria-label="Lista de produtos e serviços">
              <thead>
                <tr>
                  <th scope="col">Nome</th>
                  <th scope="col">Valor Unitário</th>
                  <th scope="col">Categoria</th>
                  <th scope="col">Ações</th>
                </tr>
              </thead>
              <tbody>
                {itensFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="table-empty">Nenhum item encontrado.</td>
                  </tr>
                ) : itensFiltrados.map(item => (
                  <tr key={item.id} className={editando?.id === item.id ? 'row-editing' : ''}>
                    <td>{item.descricao}</td>
                    <td>{fmtBRL(item.preco_padrao)}</td>
                    <td>
                      <span className={`cat-badge cat-badge--${item.categoria.toLowerCase()}`}>
                        {CATEGORIA_LABEL[item.categoria]}
                      </span>
                    </td>
                    <td>
                      <div className="pd-acoes">
                        <button
                          className="btn-acao"
                          onClick={() => iniciarEdicao(item)}
                          aria-label={`Editar ${item.descricao}`}
                        >
                          Editar
                        </button>
                        <button
                          className="btn-acao btn-acao--perigo"
                          onClick={() => setConfirmandoExcluir(item.id)}
                          aria-label={`Excluir ${item.descricao}`}
                        >
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Formulário */}
          <section className="pd-form-section" aria-label={editando ? 'Editar item' : 'Cadastrar item'}>
            <h2 className="pd-form-titulo">
              {editando ? `Editar: ${editando.descricao}` : 'Cadastrar / Editar Produto / Serviço'}
            </h2>
            <form onSubmit={salvar} noValidate>
              <div className="pd-form-grid">
                <div className="form-field pd-form-field--full">
                  <label className="form-label" htmlFor="pd-descricao">Nome</label>
                  <input
                    id="pd-descricao"
                    name="descricao"
                    className="form-input"
                    placeholder="Nome do Produto / Serviço"
                    value={form.descricao}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="pd-preco">Valor Unitário</label>
                  <input
                    id="pd-preco"
                    name="preco_padrao"
                    type="number"
                    min={0}
                    step="0.01"
                    className="form-input"
                    placeholder="0,00"
                    value={form.preco_padrao}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="pd-categoria">Categoria</label>
                  <select
                    id="pd-categoria"
                    name="categoria"
                    className="form-input"
                    value={form.categoria}
                    onChange={handleForm}
                  >
                    <option value="PRODUTO">Produto</option>
                    <option value="SERVICO">Serviço</option>
                  </select>
                </div>
              </div>

              {erroForm && (
                <p className="page-erro" role="alert">{erroForm}</p>
              )}

              <div className="pd-form-acoes">
                <button type="submit" className="btn btn--primary" disabled={salvando}>
                  {salvando ? 'Salvando…' : 'Salvar'}
                </button>
                {editando && (
                  <button type="button" className="btn btn--ghost" onClick={cancelar}>
                    Cancelar
                  </button>
                )}
              </div>
            </form>
          </section>
        </>
      )}

      {/* Modal excluir */}
      {confirmandoExcluir && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar exclusão"
          onClick={e => { if (e.target === e.currentTarget) setConfirmandoExcluir(null) }}
        >
          <div className="modal modal--pequeno">
            <div className="modal__header">
              <h2 className="modal__titulo">Excluir item</h2>
              <button className="modal__fechar" onClick={() => setConfirmandoExcluir(null)} aria-label="Fechar">✕</button>
            </div>
            <p className="modal__corpo">
              Tem certeza que deseja excluir este item? Esta ação não pode ser desfeita.
            </p>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setConfirmandoExcluir(null)}>Cancelar</button>
              <button className="btn btn--perigo" onClick={excluir} disabled={excluindo}>
                {excluindo ? 'Excluindo…' : 'Excluir'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Produtos
