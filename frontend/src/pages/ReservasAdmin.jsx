import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import './QuartosAdmin.css'
import './ReservasAdmin.css'

const STATUS_LABEL = {
  CONFIRMADA: 'Confirmada',
  CANCELADA: 'Cancelada',
  LISTA_ESPERA: 'Lista de Espera',
  UTILIZADA: 'Utilizada',
}

const FORM_INICIAL = { data_entrada: '', data_saida: '', status: '' }

const STATUS_EDITAVEIS = ['CONFIRMADA', 'LISTA_ESPERA']

function fmtData(iso) {
  if (!iso) return '—'
  return new Date(iso + 'T12:00').toLocaleDateString('pt-BR')
}

function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function ReservasAdmin() {
  const [reservas, setReservas] = useState([])
  const [tiposMap, setTiposMap] = useState({})
  const [clientesMap, setClientesMap] = useState({})
  const [filtroStatus, setFiltroStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editando, setEditando] = useState(null)
  const [form, setForm] = useState(FORM_INICIAL)
  const [salvando, setSalvando] = useState(false)
  const [erroForm, setErroForm] = useState(null)
  const [confirmandoExcluir, setConfirmandoExcluir] = useState(null)
  const [excluindo, setExcluindo] = useState(false)
  const [erroExcluir, setErroExcluir] = useState(null)
  const navigate = useNavigate()

  const role = getUserRole()
  const isGerente = role === 'GERENTE'
  const podeAcessar = role === 'GERENTE' || role === 'RECEPCIONISTA'

  const reservasFiltradas = filtroStatus
    ? reservas.filter(r => r.status === filtroStatus)
    : reservas

  useEffect(() => {
    if (!podeAcessar) return
    Promise.all([
      apiFetch('/reservas/'),
      apiFetch('/tipos-quarto/').catch(() => []),
      apiFetch('/clientes/').catch(() => []),
    ])
      .then(([reservasData, tiposData, clientesData]) => {
        setReservas(reservasData)
        const tiposM = {}
        tiposData.forEach(t => { tiposM[t.id] = t.nome })
        setTiposMap(tiposM)
        const clientesM = {}
        clientesData.forEach(c => { clientesM[c.id] = c.nome })
        setClientesMap(clientesM)
      })
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate, podeAcessar])

  function iniciarEdicao(reserva) {
    setEditando(reserva)
    setForm({ data_entrada: reserva.data_entrada, data_saida: reserva.data_saida, status: reserva.status })
    setErroForm(null)
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  }

  function cancelarEdicao() {
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
    setSalvando(true)
    setErroForm(null)
    try {
      if (form.status === 'CANCELADA' && editando.status !== 'CANCELADA') {
        const atualizada = await apiFetch(`/reservas/${editando.id}/cancelar`, { method: 'PATCH' })
        setReservas(prev => prev.map(r => r.id === atualizada.id ? atualizada : r))
      } else {
        if (!form.data_entrada || !form.data_saida) {
          setErroForm('Preencha as datas de entrada e saída.')
          setSalvando(false)
          return
        }
        if (form.data_saida <= form.data_entrada) {
          setErroForm('A data de saída deve ser posterior à data de entrada.')
          setSalvando(false)
          return
        }
        const atualizada = await apiFetch(`/reservas/${editando.id}`, {
          method: 'PUT',
          body: JSON.stringify({ data_entrada: form.data_entrada, data_saida: form.data_saida }),
        })
        setReservas(prev => prev.map(r => r.id === atualizada.id ? atualizada : r))
      }
      cancelarEdicao()
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
      await apiFetch(`/reservas/${confirmandoExcluir}`, { method: 'DELETE' })
      setReservas(prev => prev.filter(r => r.id !== confirmandoExcluir))
      if (editando?.id === confirmandoExcluir) cancelarEdicao()
      setConfirmandoExcluir(null)
    } catch (err) {
      if (err.status === 401) navigate('/login')
      else setErroExcluir(err.message)
    } finally {
      setExcluindo(false)
    }
  }

  if (!podeAcessar) {
    return (
      <div className="qa-page">
        <h1 className="qa-title">Gestão de Reservas</h1>
        <p className="qa-restrito">Acesso restrito.</p>
      </div>
    )
  }

  return (
    <div className="qa-page">
      <h1 className="qa-title">Gestão de Reservas</h1>

      {loading && (
        <div className="qa-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando reservas…</p>
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
          <div className="qa-filtro">
            <label className="qa-filtro__label" htmlFor="filtro-status">Status</label>
            <select
              id="filtro-status"
              className="form-input qa-filtro__select"
              value={filtroStatus}
              onChange={e => setFiltroStatus(e.target.value)}
            >
              <option value="">Todos</option>
              <option value="CONFIRMADA">Confirmada</option>
              <option value="LISTA_ESPERA">Lista de Espera</option>
              <option value="UTILIZADA">Utilizada</option>
              <option value="CANCELADA">Cancelada</option>
            </select>
          </div>

          <div className="table-wrapper">
            <table className="qa-table" aria-label="Lista de reservas">
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Cliente</th>
                  <th scope="col">Tipo de Quarto</th>
                  <th scope="col">Entrada</th>
                  <th scope="col">Saída</th>
                  <th scope="col">Status</th>
                  <th scope="col">Valor Previsto</th>
                  <th scope="col">Ações</th>
                </tr>
              </thead>
              <tbody>
                {reservasFiltradas.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="table-empty">Nenhuma reserva encontrada.</td>
                  </tr>
                ) : reservasFiltradas.map(r => {
                  const podeEditar = r.status === 'CONFIRMADA' || r.status === 'LISTA_ESPERA'
                  const podeExcluir = isGerente && r.status !== 'UTILIZADA'
                  return (
                    <tr key={r.id} className={editando?.id === r.id ? 'row-editing' : ''}>
                      <td>#{r.id}</td>
                      <td>{clientesMap[r.cliente_id] ?? `Cliente ${r.cliente_id}`}</td>
                      <td>{tiposMap[r.tipo_quarto_id] ?? `Tipo ${r.tipo_quarto_id}`}</td>
                      <td>{fmtData(r.data_entrada)}</td>
                      <td>{fmtData(r.data_saida)}</td>
                      <td>
                        <span className={`ra-status ra-status--${r.status.toLowerCase().replace('_', '-')}`}>
                          {STATUS_LABEL[r.status] ?? r.status}
                        </span>
                      </td>
                      <td>{formatBRL(r.valor_total_previsto)}</td>
                      <td>
                        <div className="qa-acoes">
                          {podeEditar && (
                            <button
                              className="btn-acao"
                              onClick={() => iniciarEdicao(r)}
                              aria-label={`Editar reserva #${r.id}`}
                            >
                              Editar
                            </button>
                          )}
                          {podeExcluir && (
                            <button
                              className="btn-acao btn-acao--perigo"
                              onClick={() => setConfirmandoExcluir(r.id)}
                              aria-label={`Excluir reserva #${r.id}`}
                            >
                              Excluir
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {editando && (
            <section className="qa-form-section" aria-label="Editar reserva">
              <h2 className="qa-form-titulo">Editar Reserva #{editando.id}</h2>
              <form onSubmit={salvar} noValidate>
                <div className="qa-form-grid">
                  <div className="form-field">
                    <label className="form-label" htmlFor="ra-entrada">Data de Entrada</label>
                    <input
                      id="ra-entrada"
                      name="data_entrada"
                      type="date"
                      className="form-input"
                      value={form.data_entrada}
                      onChange={handleForm}
                      disabled={form.status === 'CANCELADA'}
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label" htmlFor="ra-saida">Data de Saída</label>
                    <input
                      id="ra-saida"
                      name="data_saida"
                      type="date"
                      className="form-input"
                      value={form.data_saida}
                      onChange={handleForm}
                      disabled={form.status === 'CANCELADA'}
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label" htmlFor="ra-status">Status</label>
                    <select
                      id="ra-status"
                      name="status"
                      className="form-input"
                      value={form.status}
                      onChange={handleForm}
                    >
                      {STATUS_EDITAVEIS.includes(editando?.status) && (
                        <option value={editando.status}>{STATUS_LABEL[editando.status]}</option>
                      )}
                      {editando?.status !== 'CANCELADA' && (
                        <option value="CANCELADA">Cancelada</option>
                      )}
                    </select>
                  </div>
                </div>

                {erroForm && (
                  <p className="page-erro" role="alert">{erroForm}</p>
                )}

                <div className="qa-form-acoes">
                  <button type="submit" className="btn btn--primary" disabled={salvando}>
                    {salvando ? 'Salvando…' : 'Salvar'}
                  </button>
                  <button type="button" className="btn btn--ghost" onClick={cancelarEdicao}>
                    Cancelar
                  </button>
                </div>
              </form>
            </section>
          )}
        </>
      )}

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
              <h2 className="modal__titulo">Excluir reserva</h2>
              <button
                className="modal__fechar"
                onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }}
                aria-label="Fechar"
              >
                ✕
              </button>
            </div>
            <p className="modal__corpo">
              Tem certeza que deseja excluir esta reserva? Esta ação não pode ser desfeita.
            </p>
            {erroExcluir && (
              <p className="page-erro" role="alert" style={{ margin: '0 24px' }}>{erroExcluir}</p>
            )}
            <div className="modal__footer">
              <button
                className="btn btn--ghost"
                onClick={() => { setConfirmandoExcluir(null); setErroExcluir(null) }}
              >
                Cancelar
              </button>
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
