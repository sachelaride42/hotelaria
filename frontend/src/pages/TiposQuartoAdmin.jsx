import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import './TiposQuartoAdmin.css'

const FORM_INICIAL = { nome: '', descricao: '', precoBaseDiaria: '', capacidade: '' }

function fmtBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function TiposQuartoAdmin() {
  const [tipos, setTipos]                         = useState([])
  const [filtro, setFiltro]                       = useState('')
  const [loading, setLoading]                     = useState(true)
  const [error, setError]                         = useState(null)
  const [editando, setEditando]                   = useState(null)
  const [form, setForm]                           = useState(FORM_INICIAL)
  const [salvando, setSalvando]                   = useState(false)
  const [erroForm, setErroForm]                   = useState(null)
  const [confirmandoExcluir, setConfirmandoExcluir] = useState(null)
  const [excluindo, setExcluindo]                 = useState(false)
  const [erroExcluir, setErroExcluir]             = useState(null)
  const navigate = useNavigate()

  const role = getUserRole()

  const tiposFiltrados = filtro.trim()
    ? tipos.filter(t => t.nome.toLowerCase().includes(filtro.toLowerCase()))
    : tipos

  useEffect(() => {
    if (role !== 'GERENTE') return
    apiFetch('/tipos-quarto/')
      .then(setTipos)
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate, role])

  function iniciarEdicao(tipo) {
    setEditando(tipo)
    setForm({
      nome: tipo.nome,
      descricao: tipo.descricao ?? '',
      precoBaseDiaria: String(tipo.precoBaseDiaria),
      capacidade: String(tipo.capacidade),
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
    if (!form.nome.trim() || !form.precoBaseDiaria || Number(form.precoBaseDiaria) <= 0 || !form.capacidade || Number(form.capacidade) < 1) {
      setErroForm('Preencha nome, preço base (> 0) e capacidade (≥ 1).')
      return
    }
    setSalvando(true)
    setErroForm(null)
    const payload = {
      nome: form.nome.trim(),
      descricao: form.descricao.trim() || null,
      precoBaseDiaria: Number(form.precoBaseDiaria),
      capacidade: Number(form.capacidade),
    }
    try {
      if (editando) {
        const atualizado = await apiFetch(`/tipos-quarto/${editando.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
        setTipos(prev => prev.map(t => t.id === atualizado.id ? atualizado : t))
      } else {
        const novo = await apiFetch('/tipos-quarto/', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setTipos(prev => [...prev, novo])
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
    setErroExcluir(null)
    try {
      await apiFetch(`/tipos-quarto/${confirmandoExcluir}`, { method: 'DELETE' })
      setTipos(prev => prev.filter(t => t.id !== confirmandoExcluir))
      if (editando?.id === confirmandoExcluir) cancelar()
      setConfirmandoExcluir(null)
    } catch (err) {
      if (err.status === 401) navigate('/login')
      else setErroExcluir(err.message)
    } finally {
      setExcluindo(false)
    }
  }

  if (role !== 'GERENTE') {
    return (
      <div className="tq-page">
        <h1 className="tq-title">Gestão de Tipos de Quarto</h1>
        <p className="tq-restrito">Acesso restrito a administradores.</p>
      </div>
    )
  }

  return (
    <div className="tq-page">
      <h1 className="tq-title">Gestão de Tipos de Quarto</h1>

      {loading && (
        <div className="tq-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando tipos de quarto…</p>
        </div>
      )}

      {error && (
        <div className="tq-feedback tq-feedback--error" role="alert">
          <p>Não foi possível carregar os dados.</p>
          <p className="tq-error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Busca */}
          <div className="tq-busca">
            <label className="tq-busca__label" htmlFor="tq-filtro">Buscar Tipo de Quarto</label>
            <div className="tq-busca__row">
              <input
                id="tq-filtro"
                className="form-input tq-busca__input"
                placeholder="Pesquisar pelo nome…"
                value={filtro}
                onChange={e => setFiltro(e.target.value)}
              />
            </div>
          </div>

          {/* Tabela */}
          <div className="table-wrapper">
            <table className="tq-table" aria-label="Lista de tipos de quarto">
              <thead>
                <tr>
                  <th scope="col">Nome</th>
                  <th scope="col">Descrição</th>
                  <th scope="col">Preço Base Diária</th>
                  <th scope="col">Capacidade</th>
                  <th scope="col">Ações</th>
                </tr>
              </thead>
              <tbody>
                {tiposFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="table-empty">Nenhum tipo de quarto encontrado.</td>
                  </tr>
                ) : tiposFiltrados.map(tipo => (
                  <tr key={tipo.id} className={editando?.id === tipo.id ? 'row-editing' : ''}>
                    <td>{tipo.nome}</td>
                    <td>{tipo.descricao ?? '—'}</td>
                    <td>{fmtBRL(tipo.precoBaseDiaria)}</td>
                    <td>{tipo.capacidade} {tipo.capacidade === 1 ? 'pessoa' : 'pessoas'}</td>
                    <td>
                      <div className="tq-acoes">
                        <button
                          className="btn-acao"
                          onClick={() => iniciarEdicao(tipo)}
                          aria-label={`Editar ${tipo.nome}`}
                        >
                          Editar
                        </button>
                        <button
                          className="btn-acao btn-acao--perigo"
                          onClick={() => { setConfirmandoExcluir(tipo.id); setErroExcluir(null) }}
                          aria-label={`Excluir ${tipo.nome}`}
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
          <section className="tq-form-section" aria-label={editando ? 'Editar tipo de quarto' : 'Cadastrar tipo de quarto'}>
            <h2 className="tq-form-titulo">
              {editando ? `Editar: ${editando.nome}` : 'Cadastrar / Editar Tipo de Quarto'}
            </h2>
            <form onSubmit={salvar} noValidate>
              <div className="tq-form-grid">
                <div className="form-field tq-form-field--full">
                  <label className="form-label" htmlFor="tq-nome">Nome</label>
                  <input
                    id="tq-nome"
                    name="nome"
                    className="form-input"
                    placeholder="Nome do tipo de quarto"
                    value={form.nome}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field tq-form-field--full">
                  <label className="form-label" htmlFor="tq-descricao">Descrição <span className="tq-opcional">(opcional)</span></label>
                  <input
                    id="tq-descricao"
                    name="descricao"
                    className="form-input"
                    placeholder="Descrição do tipo de quarto"
                    value={form.descricao}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="tq-preco">Preço Base Diária</label>
                  <input
                    id="tq-preco"
                    name="precoBaseDiaria"
                    type="number"
                    min={0.01}
                    step="0.01"
                    className="form-input"
                    placeholder="0,00"
                    value={form.precoBaseDiaria}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="tq-capacidade">Capacidade (pessoas)</label>
                  <input
                    id="tq-capacidade"
                    name="capacidade"
                    type="number"
                    min={1}
                    step={1}
                    className="form-input"
                    placeholder="Ex: 2"
                    value={form.capacidade}
                    onChange={handleForm}
                  />
                </div>
              </div>

              {erroForm && (
                <p className="page-erro" role="alert">{erroForm}</p>
              )}

              <div className="tq-form-acoes">
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
          onClick={e => { if (e.target === e.currentTarget) { setConfirmandoExcluir(null); setErroExcluir(null) } }}
        >
          <div className="modal modal--pequeno">
            <div className="modal__header">
              <h2 className="modal__titulo">Excluir tipo de quarto</h2>
              <button className="modal__fechar" onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }} aria-label="Fechar">✕</button>
            </div>
            <p className="modal__corpo">
              Tem certeza que deseja excluir este tipo de quarto? Esta ação não pode ser desfeita.
            </p>
            {erroExcluir && (
              <p className="page-erro" role="alert" style={{ margin: '0 24px' }}>{erroExcluir}</p>
            )}
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }}>Cancelar</button>
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

export default TiposQuartoAdmin
