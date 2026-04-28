import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import './UsuariosAdmin.css'

const TIPO_LABEL = { GERENTE: 'Gerente', RECEPCIONISTA: 'Recepcionista' }
const FORM_INICIAL = { nome: '', email: '', tipo: 'RECEPCIONISTA', senha: '' }

function UsuariosAdmin() {
  const [usuarios, setUsuarios]                   = useState([])
  const [filtroNome, setFiltroNome]               = useState('')
  const [filtroTipo, setFiltroTipo]               = useState('')
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

  const usuariosFiltrados = usuarios.filter(u => {
    const nomeOk = !filtroNome.trim() || u.nome.toLowerCase().includes(filtroNome.toLowerCase())
    const tipoOk = !filtroTipo || u.tipo === filtroTipo
    return nomeOk && tipoOk
  })

  useEffect(() => {
    if (role !== 'GERENTE') return
    apiFetch('/usuarios/')
      .then(setUsuarios)
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate, role])

  function iniciarEdicao(usuario) {
    setEditando(usuario)
    setForm({
      nome: usuario.nome,
      email: usuario.email,
      tipo: usuario.tipo,
      senha: '',
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
    if (!form.nome.trim() || !form.email.trim()) {
      setErroForm('Preencha nome e e-mail.')
      return
    }
    if (!editando && !form.senha) {
      setErroForm('A senha é obrigatória para novos usuários.')
      return
    }
    setSalvando(true)
    setErroForm(null)
    const payload = {
      nome: form.nome.trim(),
      email: form.email.trim(),
      tipo: form.tipo,
    }
    if (form.senha) payload.senha = form.senha
    try {
      if (editando) {
        const atualizado = await apiFetch(`/usuarios/${editando.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
        setUsuarios(prev => prev.map(u => u.id === atualizado.id ? atualizado : u))
      } else {
        const novo = await apiFetch('/usuarios/', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setUsuarios(prev => [...prev, novo])
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
      await apiFetch(`/usuarios/${confirmandoExcluir}`, { method: 'DELETE' })
      setUsuarios(prev => prev.filter(u => u.id !== confirmandoExcluir))
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
      <div className="us-page">
        <h1 className="us-title">Gestão de Usuários</h1>
        <p className="us-restrito">Acesso restrito a administradores.</p>
      </div>
    )
  }

  return (
    <div className="us-page">
      <h1 className="us-title">Gestão de Usuários</h1>

      {loading && (
        <div className="us-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando usuários…</p>
        </div>
      )}

      {error && (
        <div className="us-feedback us-feedback--error" role="alert">
          <p>Não foi possível carregar os dados.</p>
          <p className="us-error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Filtros */}
          <div className="us-filtros">
            <div className="us-filtros__grupo">
              <label className="us-busca__label" htmlFor="us-filtro-nome">Buscar Usuário</label>
              <input
                id="us-filtro-nome"
                className="form-input us-busca__input"
                placeholder="Pesquisar pelo nome…"
                value={filtroNome}
                onChange={e => setFiltroNome(e.target.value)}
              />
            </div>
            <div className="us-filtros__grupo">
              <label className="us-busca__label" htmlFor="us-filtro-tipo">Tipo</label>
              <select
                id="us-filtro-tipo"
                className="form-input us-filtro__select"
                value={filtroTipo}
                onChange={e => setFiltroTipo(e.target.value)}
              >
                <option value="">Todos</option>
                <option value="GERENTE">Gerente</option>
                <option value="RECEPCIONISTA">Recepcionista</option>
              </select>
            </div>
          </div>

          {/* Tabela */}
          <div className="table-wrapper">
            <table className="us-table" aria-label="Lista de usuários">
              <thead>
                <tr>
                  <th scope="col">Nome</th>
                  <th scope="col">E-mail</th>
                  <th scope="col">Tipo</th>
                  <th scope="col">Ações</th>
                </tr>
              </thead>
              <tbody>
                {usuariosFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="table-empty">Nenhum usuário encontrado.</td>
                  </tr>
                ) : usuariosFiltrados.map(usuario => (
                  <tr key={usuario.id} className={editando?.id === usuario.id ? 'row-editing' : ''}>
                    <td>{usuario.nome}</td>
                    <td>{usuario.email}</td>
                    <td>
                      <span className={`us-badge us-badge--${usuario.tipo.toLowerCase()}`}>
                        {TIPO_LABEL[usuario.tipo]}
                      </span>
                    </td>
                    <td>
                      <div className="us-acoes">
                        <button
                          className="btn-acao"
                          onClick={() => iniciarEdicao(usuario)}
                          aria-label={`Editar ${usuario.nome}`}
                        >
                          Editar
                        </button>
                        <button
                          className="btn-acao btn-acao--perigo"
                          onClick={() => { setConfirmandoExcluir(usuario.id); setErroExcluir(null) }}
                          aria-label={`Excluir ${usuario.nome}`}
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
          <section className="us-form-section" aria-label={editando ? 'Editar usuário' : 'Cadastrar usuário'}>
            <h2 className="us-form-titulo">
              {editando ? `Editar: ${editando.nome}` : 'Cadastrar / Editar Usuário'}
            </h2>
            <form onSubmit={salvar} noValidate>
              <div className="us-form-grid">
                <div className="form-field us-form-field--full">
                  <label className="form-label" htmlFor="us-nome">Nome</label>
                  <input
                    id="us-nome"
                    name="nome"
                    className="form-input"
                    placeholder="Nome completo"
                    value={form.nome}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field us-form-field--full">
                  <label className="form-label" htmlFor="us-email">E-mail</label>
                  <input
                    id="us-email"
                    name="email"
                    type="email"
                    className="form-input"
                    placeholder="email@exemplo.com"
                    value={form.email}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="us-tipo">Tipo</label>
                  <select
                    id="us-tipo"
                    name="tipo"
                    className="form-input"
                    value={form.tipo}
                    onChange={handleForm}
                  >
                    <option value="RECEPCIONISTA">Recepcionista</option>
                    <option value="GERENTE">Gerente</option>
                  </select>
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="us-senha">
                    Senha {editando && <span className="us-opcional">(deixe em branco para manter)</span>}
                  </label>
                  <input
                    id="us-senha"
                    name="senha"
                    type="password"
                    className="form-input"
                    placeholder={editando ? 'Deixe em branco para manter' : 'Mínimo 6 caracteres'}
                    value={form.senha}
                    onChange={handleForm}
                    autoComplete="new-password"
                  />
                </div>
              </div>

              {erroForm && (
                <p className="page-erro" role="alert">{erroForm}</p>
              )}

              <div className="us-form-acoes">
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
              <h2 className="modal__titulo">Excluir usuário</h2>
              <button className="modal__fechar" onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }} aria-label="Fechar">✕</button>
            </div>
            <p className="modal__corpo">
              Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.
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

export default UsuariosAdmin
