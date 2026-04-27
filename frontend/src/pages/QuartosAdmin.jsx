import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import './QuartosAdmin.css'

const OCUPACAO_LABEL = { LIVRE: 'Livre', OCUPADO: 'Ocupado', MANUTENCAO: 'Manutenção' }
const LIMPEZA_LABEL  = { LIMPO: 'Limpo', SUJO: 'Sujo' }
const FORM_INICIAL   = { numero: '', andar: '', tipo_quarto_id: '', status_ocupacao: 'LIVRE', status_limpeza: 'LIMPO' }

function QuartosAdmin() {
  const [quartos, setQuartos]                   = useState([])
  const [tipos, setTipos]                       = useState([])
  const [tiposMap, setTiposMap]                 = useState({})
  const [filtroTipo, setFiltroTipo]             = useState('')
  const [loading, setLoading]                   = useState(true)
  const [error, setError]                       = useState(null)
  const [editando, setEditando]                 = useState(null)
  const [form, setForm]                         = useState(FORM_INICIAL)
  const [salvando, setSalvando]                 = useState(false)
  const [erroForm, setErroForm]                 = useState(null)
  const [confirmandoExcluir, setConfirmandoExcluir] = useState(null)
  const [excluindo, setExcluindo]               = useState(false)
  const [erroExcluir, setErroExcluir]           = useState(null)
  const navigate = useNavigate()

  const role = getUserRole()

  const quartosFiltrados = filtroTipo
    ? quartos.filter(q => String(q.tipo_quarto_id) === filtroTipo)
    : quartos

  useEffect(() => {
    if (role !== 'GERENTE') return
    Promise.all([
      apiFetch('/quartos/'),
      apiFetch('/tipos-quarto/').catch(() => []),
    ])
      .then(([quartosData, tiposData]) => {
        setQuartos(quartosData)
        setTipos(tiposData)
        const map = {}
        tiposData.forEach(t => { map[t.id] = t.nome })
        setTiposMap(map)
      })
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate, role])

  function iniciarEdicao(quarto) {
    setEditando(quarto)
    setForm({
      numero: quarto.numero,
      andar: String(quarto.andar),
      tipo_quarto_id: String(quarto.tipo_quarto_id),
      status_ocupacao: quarto.status_ocupacao,
      status_limpeza: quarto.status_limpeza,
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
    if (!form.numero.trim() || !form.andar || !form.tipo_quarto_id) {
      setErroForm('Preencha todos os campos obrigatórios.')
      return
    }
    setSalvando(true)
    setErroForm(null)
    try {
      if (editando) {
        let current = await apiFetch(`/quartos/${editando.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            numero: form.numero.trim(),
            andar: Number(form.andar),
            tipo_quarto_id: Number(form.tipo_quarto_id),
          }),
        })
        if (form.status_ocupacao !== editando.status_ocupacao) {
          current = await apiFetch(`/quartos/${editando.id}/status-ocupacao`, {
            method: 'PATCH',
            body: JSON.stringify({ status_ocupacao: form.status_ocupacao, versao: current.versao }),
          })
        }
        if (form.status_limpeza !== editando.status_limpeza) {
          current = await apiFetch(`/quartos/${editando.id}/status-limpeza`, {
            method: 'PATCH',
            body: JSON.stringify({ status_limpeza: form.status_limpeza, versao: current.versao }),
          })
        }
        setQuartos(prev => prev.map(q => q.id === current.id ? current : q))
      } else {
        const novo = await apiFetch('/quartos/', {
          method: 'POST',
          body: JSON.stringify({
            numero: form.numero.trim(),
            andar: Number(form.andar),
            tipo_quarto_id: Number(form.tipo_quarto_id),
          }),
        })
        setQuartos(prev => [...prev, novo])
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
      await apiFetch(`/quartos/${confirmandoExcluir}`, { method: 'DELETE' })
      setQuartos(prev => prev.filter(q => q.id !== confirmandoExcluir))
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
      <div className="qa-page">
        <h1 className="qa-title">Gestão de Quartos</h1>
        <p className="qa-restrito">Acesso restrito a administradores.</p>
      </div>
    )
  }

  return (
    <div className="qa-page">
      <h1 className="qa-title">Gestão de Quartos</h1>

      {loading && (
        <div className="qa-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando quartos…</p>
        </div>
      )}

      {error && (
        <div className="qa-feedback qa-feedback--error" role="alert">
          <p>Não foi possível carregar os dados.</p>
          <p className="qa-error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Filtro por tipo */}
          <div className="qa-filtro">
            <label className="qa-filtro__label" htmlFor="filtro-tipo">
              Selecione o Filtro
            </label>
            <select
              id="filtro-tipo"
              className="form-input qa-filtro__select"
              value={filtroTipo}
              onChange={e => setFiltroTipo(e.target.value)}
            >
              <option value="">Todos os tipos</option>
              {tipos.map(t => (
                <option key={t.id} value={String(t.id)}>{t.nome}</option>
              ))}
            </select>
          </div>

          {/* Tabela */}
          <div className="table-wrapper">
            <table className="qa-table" aria-label="Lista de quartos">
              <thead>
                <tr>
                  <th scope="col">Número</th>
                  <th scope="col">Tipo</th>
                  <th scope="col">Andar</th>
                  <th scope="col">Status Hospedagem</th>
                  <th scope="col">Status Limpeza</th>
                  <th scope="col">Ações</th>
                </tr>
              </thead>
              <tbody>
                {quartosFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="table-empty">Nenhum quarto encontrado.</td>
                  </tr>
                ) : quartosFiltrados.map(q => (
                  <tr key={q.id} className={editando?.id === q.id ? 'row-editing' : ''}>
                    <td>{q.numero}</td>
                    <td>{tiposMap[q.tipo_quarto_id] ?? `Tipo ${q.tipo_quarto_id}`}</td>
                    <td>{q.andar}º</td>
                    <td>
                      <span className={`badge badge--${q.status_ocupacao.toLowerCase()}`}>
                        {OCUPACAO_LABEL[q.status_ocupacao]}
                      </span>
                    </td>
                    <td>
                      <span className={`limpeza-badge limpeza-badge--${q.status_limpeza.toLowerCase()}`}>
                        {LIMPEZA_LABEL[q.status_limpeza]}
                      </span>
                    </td>
                    <td>
                      <div className="qa-acoes">
                        <button
                          className="btn-acao"
                          onClick={() => iniciarEdicao(q)}
                          aria-label={`Editar quarto ${q.numero}`}
                        >
                          Editar
                        </button>
                        <button
                          className="btn-acao btn-acao--perigo"
                          onClick={() => setConfirmandoExcluir(q.id)}
                          aria-label={`Excluir quarto ${q.numero}`}
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
          <section className="qa-form-section" aria-label={editando ? 'Editar quarto' : 'Cadastrar quarto'}>
            <h2 className="qa-form-titulo">
              {editando ? `Editar Quarto ${editando.numero}` : 'Cadastrar Quarto'}
            </h2>
            <form onSubmit={salvar} noValidate>
              <div className="qa-form-grid">
                <div className="form-field">
                  <label className="form-label" htmlFor="qa-numero">Número</label>
                  <input
                    id="qa-numero"
                    name="numero"
                    className="form-input"
                    placeholder="Ex: 101"
                    value={form.numero}
                    onChange={handleForm}
                    maxLength={10}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="qa-andar">Andar</label>
                  <input
                    id="qa-andar"
                    name="andar"
                    type="number"
                    min={1}
                    className="form-input"
                    placeholder="Ex: 1"
                    value={form.andar}
                    onChange={handleForm}
                  />
                </div>
                <div className="form-field">
                  <label className="form-label" htmlFor="qa-tipo">Tipo</label>
                  <select
                    id="qa-tipo"
                    name="tipo_quarto_id"
                    className="form-input"
                    value={form.tipo_quarto_id}
                    onChange={handleForm}
                  >
                    <option value="">Selecione…</option>
                    {tipos.map(t => (
                      <option key={t.id} value={String(t.id)}>{t.nome}</option>
                    ))}
                  </select>
                </div>

                {editando && (
                  <>
                    <div className="form-field">
                      <label className="form-label" htmlFor="qa-status-ocupacao">Status Hospedagem</label>
                      <select
                        id="qa-status-ocupacao"
                        name="status_ocupacao"
                        className="form-input"
                        value={form.status_ocupacao}
                        onChange={handleForm}
                      >
                        <option value="LIVRE">Livre</option>
                        <option value="OCUPADO">Ocupado</option>
                        <option value="MANUTENCAO">Manutenção</option>
                      </select>
                    </div>
                    <div className="form-field">
                      <label className="form-label" htmlFor="qa-status-limpeza">Status Limpeza</label>
                      <select
                        id="qa-status-limpeza"
                        name="status_limpeza"
                        className="form-input"
                        value={form.status_limpeza}
                        onChange={handleForm}
                      >
                        <option value="LIMPO">Limpo</option>
                        <option value="SUJO">Sujo</option>
                      </select>
                    </div>
                  </>
                )}
              </div>

              {erroForm && (
                <p className="page-erro" role="alert">{erroForm}</p>
              )}

              <div className="qa-form-acoes">
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
              <h2 className="modal__titulo">Excluir quarto</h2>
              <button className="modal__fechar" onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }} aria-label="Fechar">✕</button>
            </div>
            <p className="modal__corpo">
              Tem certeza que deseja excluir este quarto? Esta ação não pode ser desfeita.
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

export default QuartosAdmin
