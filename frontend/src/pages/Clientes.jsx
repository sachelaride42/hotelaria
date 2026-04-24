import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import { maskCPF, maskTelefone, stripMask } from '../utils/masks'
import './Clientes.css'

function fmtData(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR')
}

function fmtBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const STATUS_LABEL = {
  ATIVA: 'Ativa',
  FINALIZADA: 'Finalizada',
  CANCELADA: 'Cancelada',
}

export default function Clientes() {
  const navigate = useNavigate()
  const isGerente = getUserRole() === 'GERENTE'

  const [clientes, setClientes] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erroLista, setErroLista] = useState('')

  const [filtro, setFiltro] = useState('')

  /* ── Formulário ── */
  const [clienteEditando, setClienteEditando] = useState(null) // null = modo novo
  const [form, setForm] = useState({ nome: '', cpf: '', email: '', telefone: '' })
  const [salvando, setSalvando] = useState(false)
  const [erroForm, setErroForm] = useState('')

  /* ── Modal histórico ── */
  const [clienteHistorico, setClienteHistorico] = useState(null)
  const [hospedagens, setHospedagens] = useState([])
  const [loadingHistorico, setLoadingHistorico] = useState(false)

  /* ── Confirmação de exclusão ── */
  const [confirmandoExcluir, setConfirmandoExcluir] = useState(null)
  const [excluindo, setExcluindo] = useState(false)
  const [erroExcluir, setErroExcluir] = useState('')

  /* ── Carregar clientes ── */
  async function carregarClientes() {
    setCarregando(true)
    setErroLista('')
    try {
      const data = await apiFetch('/clientes/')
      setClientes(data)
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroLista('Erro ao carregar clientes.')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => { carregarClientes() }, [])

  /* ── Filtragem local ── */
  const termo = filtro.trim().toLowerCase()
  const termoDigitos = stripMask(termo)
  const clientesFiltrados = termo
    ? clientes.filter(c =>
        c.nome.toLowerCase().includes(termo) ||
        (termoDigitos && c.cpf && c.cpf.includes(termoDigitos)) ||
        (c.email && c.email.toLowerCase().includes(termo))
      )
    : clientes

  /* ── Formulário ── */
  function iniciarEdicao(cliente) {
    setClienteEditando(cliente)
    setForm({
      nome: cliente.nome,
      cpf: cliente.cpf ? maskCPF(cliente.cpf) : '',
      email: cliente.email ?? '',
      telefone: cliente.telefone ?? '',
    })
    setErroForm('')
    document.getElementById('form-cliente')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function cancelarForm() {
    setClienteEditando(null)
    setForm({ nome: '', cpf: '', email: '', telefone: '' })
    setErroForm('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErroForm('')
    setSalvando(true)
    try {
      const telRaw = form.telefone.startsWith('+')
        ? form.telefone.trim()
        : stripMask(form.telefone)
      const payload = { nome: form.nome.trim(), telefone: telRaw }
      if (form.cpf.trim()) payload.cpf = stripMask(form.cpf)
      if (form.email.trim()) payload.email = form.email.trim()

      if (clienteEditando) {
        await apiFetch(`/clientes/${clienteEditando.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
      } else {
        await apiFetch('/clientes/', { method: 'POST', body: JSON.stringify(payload) })
      }
      cancelarForm()
      await carregarClientes()
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroForm(err.message)
    } finally {
      setSalvando(false)
    }
  }

  /* ── Histórico ── */
  async function abrirHistorico(cliente) {
    setClienteHistorico(cliente)
    setHospedagens([])
    setLoadingHistorico(true)
    try {
      const data = await apiFetch(`/hospedagens/?cliente_id=${cliente.id}`)
      setHospedagens(data)
    } catch {
      setHospedagens([])
    } finally {
      setLoadingHistorico(false)
    }
  }

  /* ── Exclusão ── */
  async function confirmarExcluir() {
    if (!confirmandoExcluir) return
    setExcluindo(true)
    setErroExcluir('')
    try {
      await apiFetch(`/clientes/${confirmandoExcluir.id}`, { method: 'DELETE' })
      setConfirmandoExcluir(null)
      await carregarClientes()
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroExcluir(err.message)
    } finally {
      setExcluindo(false)
    }
  }

  return (
    <div className="clientes-page">
      <h1 className="page-title">Gestão de Clientes</h1>

      {/* ── Busca ── */}
      <section className="clientes-busca">
        <p className="clientes-busca__label">Filtre o Cliente</p>
        <div className="clientes-busca__row">
          <input
            className="form-input clientes-busca__input"
            placeholder="Buscar por Nome, CPF ou Email"
            value={filtro}
            onChange={e => setFiltro(e.target.value)}
            aria-label="Buscar cliente"
          />
        </div>
      </section>

      {/* ── Tabela ── */}
      <section className="clientes-tabela-wrap">
        {carregando && <p className="clientes-feedback">Carregando…</p>}
        {erroLista && <p className="clientes-feedback clientes-feedback--erro">{erroLista}</p>}

        {!carregando && !erroLista && (
          clientesFiltrados.length === 0 ? (
            <p className="clientes-feedback">Nenhum cliente encontrado.</p>
          ) : (
            <table className="clientes-tabela">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>CPF</th>
                  <th>Email</th>
                  <th>Telefone</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {clientesFiltrados.map(c => (
                  <tr key={c.id}>
                    <td>{c.nome}</td>
                    <td>{c.cpf ? maskCPF(c.cpf) : '—'}</td>
                    <td>{c.email || '—'}</td>
                    <td>{c.telefone || '—'}</td>
                    <td className="clientes-tabela__acoes">
                      <button
                        className="btn-acao"
                        onClick={() => iniciarEdicao(c)}
                        aria-label={`Editar ${c.nome}`}
                      >
                        Editar
                      </button>
                      <button
                        className="btn-acao"
                        onClick={() => abrirHistorico(c)}
                        aria-label={`Histórico de ${c.nome}`}
                      >
                        Histórico
                      </button>
                      {isGerente && (
                        <button
                          className="btn-acao btn-acao--perigo"
                          onClick={() => { setErroExcluir(''); setConfirmandoExcluir(c) }}
                          aria-label={`Excluir ${c.nome}`}
                        >
                          Excluir
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}
      </section>

      {/* ── Formulário Cadastrar / Editar ── */}
      <section className="clientes-form-section" id="form-cliente">
        <h2 className="clientes-form-section__titulo">
          {clienteEditando ? `Editar Cliente — ${clienteEditando.nome}` : 'Cadastrar Novo Cliente'}
        </h2>
        <form className="clientes-form" onSubmit={handleSubmit} noValidate>
          <div className="clientes-form__grid">
            <div className="form-field">
              <label className="form-label" htmlFor="cf-nome">Nome *</label>
              <input
                id="cf-nome"
                className="form-input"
                required
                placeholder="(Obrigatório)"
                value={form.nome}
                onChange={e => setForm(f => ({ ...f, nome: e.target.value }))}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="cf-cpf">CPF</label>
              <input
                id="cf-cpf"
                className="form-input"
                inputMode="numeric"
                placeholder="###.###.###-##"
                value={form.cpf}
                onChange={e => setForm(f => ({ ...f, cpf: maskCPF(e.target.value) }))}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="cf-email">Email</label>
              <input
                id="cf-email"
                className="form-input"
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="cf-telefone">
                Telefone *
                {form.telefone.startsWith('+') && (
                  <span className="form-label__hint"> — internacional</span>
                )}
              </label>
              <input
                id="cf-telefone"
                className="form-input"
                placeholder="(##) ######-####"
                value={form.telefone}
                onChange={e => {
                  const v = e.target.value
                  setForm(f => ({ ...f, telefone: v.startsWith('+') ? v : maskTelefone(v) }))
                }}
              />
            </div>
          </div>
          {erroForm && <p className="form-erro" role="alert">{erroForm}</p>}
          <div className="clientes-form__acoes">
            <button
              type="submit"
              className="btn btn--primary"
              disabled={salvando || !form.nome.trim() || !form.telefone.trim()}
            >
              {salvando ? 'Salvando…' : 'Salvar'}
            </button>
            <button type="button" className="btn btn--ghost" onClick={cancelarForm}>
              Cancelar
            </button>
          </div>
        </form>
      </section>

      {/* ── Modal Histórico ── */}
      {clienteHistorico && (
        <div className="modal-overlay" role="dialog" aria-modal="true"
          aria-label={`Histórico de ${clienteHistorico.nome}`}>
          <div className="modal">
            <div className="modal__header">
              <h2 className="modal__titulo">Histórico — {clienteHistorico.nome}</h2>
              <button
                className="modal__fechar"
                onClick={() => setClienteHistorico(null)}
                aria-label="Fechar histórico"
              >
                ✕
              </button>
            </div>
            {loadingHistorico && <p className="clientes-feedback">Carregando…</p>}
            {!loadingHistorico && hospedagens.length === 0 && (
              <p className="clientes-feedback">Nenhuma hospedagem registrada.</p>
            )}
            {!loadingHistorico && hospedagens.length > 0 && (
              <table className="clientes-tabela">
                <thead>
                  <tr>
                    <th>Nº</th>
                    <th>Quarto</th>
                    <th>Check-in</th>
                    <th>Checkout</th>
                    <th>Status</th>
                    <th>Valor Total</th>
                  </tr>
                </thead>
                <tbody>
                  {hospedagens.map(h => (
                    <tr key={h.id}>
                      <td>#{h.id}</td>
                      <td>#{h.quarto_id}</td>
                      <td>{fmtData(h.data_checkin)}</td>
                      <td>{h.data_checkout_real ? fmtData(h.data_checkout_real) : fmtData(h.data_checkout_previsto) + ' (prev.)'}</td>
                      <td>
                        <span className={`status-badge status-badge--${h.status.toLowerCase()}`}>
                          {STATUS_LABEL[h.status] ?? h.status}
                        </span>
                      </td>
                      <td>{fmtBRL(h.valor_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setClienteHistorico(null)}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Diálogo de confirmação de exclusão ── */}
      {confirmandoExcluir && (
        <div className="modal-overlay" role="dialog" aria-modal="true"
          aria-label="Confirmar exclusão">
          <div className="modal modal--pequeno">
            <div className="modal__header">
              <h2 className="modal__titulo">Excluir cliente</h2>
            </div>
            <p className="modal__corpo">
              Excluir <strong>{confirmandoExcluir.nome}</strong>? Esta ação não pode ser desfeita.
            </p>
            {erroExcluir && <p className="form-erro" role="alert">{erroExcluir}</p>}
            <div className="modal__footer">
              <button
                className="btn btn--ghost"
                onClick={() => setConfirmandoExcluir(null)}
                disabled={excluindo}
              >
                Cancelar
              </button>
              <button
                className="btn btn--perigo"
                onClick={confirmarExcluir}
                disabled={excluindo}
              >
                {excluindo ? 'Excluindo…' : 'Confirmar exclusão'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
