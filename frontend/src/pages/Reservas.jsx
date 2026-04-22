import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../services/api'
import { maskCPF, maskTelefone, stripMask } from '../utils/masks'
import './Reservas.css'

/* ── Helpers ── */
function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function calcularDias(entrada, saida) {
  if (!entrada || !saida) return 0
  return Math.max(0, Math.round((new Date(saida) - new Date(entrada)) / 86400000))
}

function fmtData(iso) {
  return new Date(iso + 'T12:00').toLocaleDateString('pt-BR')
}

/* ── Card de tipo de quarto ── */
function TipoCard({ tipo, quartosPorTipo, selecionado, onClick }) {
  const total = quartosPorTipo[tipo.id] ?? '?'
  return (
    <button
      type="button"
      className={`tipo-card${selecionado ? ' tipo-card--ativo' : ''}`}
      onClick={() => onClick(tipo)}
      aria-pressed={selecionado}
    >
      <span className="tipo-card__nome">{tipo.nome}</span>
      <span className="tipo-card__preco">{formatBRL(tipo.precoBaseDiaria)}/noite</span>
      <span className="tipo-card__info">
        {total} {total === 1 ? 'quarto' : 'quartos'} · cap. {tipo.capacidade} pessoas
      </span>
    </button>
  )
}

/* ── Busca de cliente com autocomplete ── */
function BuscaCliente({ onSelecionar }) {
  const [query, setQuery] = useState('')
  const [resultados, setResultados] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [aberto, setAberto] = useState(false)
  const timerRef = useRef(null)
  const wrapperRef = useRef(null)

  const buscar = useCallback(async (q) => {
    const raw = q.trim()
    if (!raw) { setResultados([]); setAberto(false); return }
    setBuscando(true)
    try {
      const ehCPF = /^\d/.test(raw)
      const valor = ehCPF ? stripMask(raw) : raw
      const campo = ehCPF ? `cpf=${encodeURIComponent(valor)}` : `nome=${encodeURIComponent(valor)}`
      const data = await apiFetch(`/clientes/?${campo}`)
      setResultados(data)
      setAberto(true)
    } catch {
      setResultados([])
    } finally {
      setBuscando(false)
    }
  }, [])

  function handleChange(e) {
    let v = e.target.value
    // Aplica máscara de CPF se o campo estiver em modo numérico
    if (/^\d/.test(v) || v === '') v = maskCPF(v)
    setQuery(v)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => buscar(v), 350)
  }

  function selecionar(cliente) {
    onSelecionar(cliente)
    setQuery(cliente.nome)
    setAberto(false)
  }

  useEffect(() => {
    function handleClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setAberto(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div className="busca-cliente" ref={wrapperRef}>
      <div className="busca-cliente__input-wrap">
        <span className="busca-cliente__icon" aria-hidden="true">🔍</span>
        <input
          type="text"
          className="form-input"
          placeholder="Nome ou CPF do cliente…"
          value={query}
          onChange={handleChange}
          onFocus={() => resultados.length > 0 && setAberto(true)}
          aria-label="Pesquisar cliente por nome ou CPF"
          aria-autocomplete="list"
          aria-expanded={aberto}
        />
        {buscando && <span className="busca-cliente__spinner" aria-hidden="true" />}
      </div>
      {aberto && resultados.length > 0 && (
        <ul className="busca-cliente__dropdown" role="listbox">
          {resultados.map(c => (
            <li key={c.id} role="option" aria-selected="false">
              <button type="button" onClick={() => selecionar(c)} className="busca-cliente__opcao">
                <strong>{c.nome}</strong>
                <span>{c.cpf ?? c.telefone}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {aberto && resultados.length === 0 && !buscando && query.trim() && (
        <p className="busca-cliente__vazio">Nenhum cliente encontrado.</p>
      )}
    </div>
  )
}

/* ── Formulário de novo cliente ── */
function FormNovoCliente({ onCriado, onCancelar }) {
  const [form, setForm] = useState({ nome: '', telefone: '', cpf: '', email: '' })
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')

  function handleNome(e) { setForm(f => ({ ...f, nome: e.target.value })) }
  function handleEmail(e) { setForm(f => ({ ...f, email: e.target.value })) }

  function handleTelefone(e) {
    const v = e.target.value
    // Se começa com '+', aceita livre (internacional); caso contrário aplica máscara
    setForm(f => ({ ...f, telefone: v.startsWith('+') ? v : maskTelefone(v) }))
  }

  function handleCPF(e) {
    setForm(f => ({ ...f, cpf: maskCPF(e.target.value) }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErro('')
    setSalvando(true)
    try {
      const telRaw = form.telefone.startsWith('+')
        ? form.telefone.trim()
        : stripMask(form.telefone)
      const payload = { nome: form.nome.trim(), telefone: telRaw }
      if (form.cpf.trim()) payload.cpf = stripMask(form.cpf)
      if (form.email.trim()) payload.email = form.email.trim()
      const cliente = await apiFetch('/clientes/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      onCriado(cliente)
    } catch (err) {
      setErro(err.message)
    } finally {
      setSalvando(false)
    }
  }

  const telInternacional = form.telefone.startsWith('+')

  return (
    <form className="form-novo-cliente" onSubmit={handleSubmit} noValidate>
      <div className="form-novo-cliente__grid">
        <div className="form-field">
          <label className="form-label">Nome *</label>
          <input name="nome" className="form-input form-input--sm" required
            value={form.nome} onChange={handleNome} placeholder="Nome completo" />
        </div>
        <div className="form-field">
          <label className="form-label">
            Telefone *
            {telInternacional && (
              <span className="form-label__hint"> — internacional</span>
            )}
          </label>
          <input name="telefone" className="form-input form-input--sm" required
            value={form.telefone} onChange={handleTelefone}
            placeholder="(11) 99999-9999 ou +1 555-0000" />
        </div>
        <div className="form-field">
          <label className="form-label">CPF</label>
          <input name="cpf" className="form-input form-input--sm"
            value={form.cpf} onChange={handleCPF}
            placeholder="000.000.000-00" inputMode="numeric" />
        </div>
        <div className="form-field">
          <label className="form-label">E-mail</label>
          <input name="email" type="email" className="form-input form-input--sm"
            value={form.email} onChange={handleEmail} placeholder="email@exemplo.com" />
        </div>
      </div>
      {erro && <p className="form-erro" role="alert">{erro}</p>}
      <div className="form-novo-cliente__actions">
        <button type="button" className="btn btn--ghost" onClick={onCancelar}>Cancelar</button>
        <button type="submit" className="btn btn--primary"
          disabled={salvando || !form.nome || !form.telefone}>
          {salvando ? 'Salvando…' : 'Salvar cliente'}
        </button>
      </div>
    </form>
  )
}

/* ── Página principal ── */
function Reservas() {
  const navigate = useNavigate()
  const hoje = new Date().toISOString().split('T')[0]
  const amanha = new Date(Date.now() + 86400000).toISOString().split('T')[0]

  // Busca
  const [dataEntrada, setDataEntrada] = useState(hoje)
  const [dataSaida, setDataSaida] = useState(amanha)
  const [nPessoas, setNPessoas] = useState(1)
  const [buscado, setBuscado] = useState(false)
  const [buscando, setBuscando] = useState(false)

  // Resultados
  const [tipos, setTipos] = useState([])
  const [quartosPorTipo, setQuartosPorTipo] = useState({})
  const [erroBusca, setErroBusca] = useState('')

  // Seleção
  const [tipoSelecionado, setTipoSelecionado] = useState(null)
  const [cliente, setCliente] = useState(null)
  const [modoCliente, setModoCliente] = useState('search')

  // Confirmação
  const [confirmando, setConfirmando] = useState(false)
  const [reservaCriada, setReservaCriada] = useState(null)
  const [erroConfirm, setErroConfirm] = useState('')
  const [semDisponibilidade, setSemDisponibilidade] = useState(false)
  const [checkandoDisp, setCheckandoDisp] = useState(false)

  async function handleSelecionarTipo(tipo) {
    setTipoSelecionado(tipo)
    setErroConfirm('')
    setReservaCriada(null)
    setSemDisponibilidade(false)
    setCheckandoDisp(true)
    try {
      const result = await apiFetch(
        `/reservas/disponibilidade/?tipo_quarto_id=${tipo.id}&data_entrada=${dataEntrada}&data_saida=${dataSaida}`
      )
      setSemDisponibilidade(!result.disponivel)
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      // Em caso de erro na checagem, deixa prosseguir (backend valida na confirmação)
    } finally {
      setCheckandoDisp(false)
    }
  }

  async function handleBuscar(e) {
    e.preventDefault()
    setErroBusca('')
    setBuscando(true)
    setTipoSelecionado(null)
    setCliente(null)
    setReservaCriada(null)
    setSemDisponibilidade(false)
    try {
      const [tiposData, quartosData] = await Promise.all([
        apiFetch(`/tipos-quarto/?capacidade_minima=${nPessoas}`),
        apiFetch('/quartos/'),
      ])
      const contagem = {}
      quartosData.forEach(q => {
        contagem[q.tipo_quarto_id] = (contagem[q.tipo_quarto_id] ?? 0) + 1
      })
      setQuartosPorTipo(contagem)
      setTipos(tiposData)
      setBuscado(true)
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroBusca(err.message)
    } finally {
      setBuscando(false)
    }
  }

  function handleCancelar() {
    setBuscado(false)
    setTipos([])
    setQuartosPorTipo({})
    setTipoSelecionado(null)
    setCliente(null)
    setModoCliente('search')
    setReservaCriada(null)
    setErroConfirm('')
    setSemDisponibilidade(false)
  }

  async function handleConfirmar() {
    if (!tipoSelecionado || !cliente) return
    setErroConfirm('')
    setSemDisponibilidade(false)
    setConfirmando(true)
    try {
      const reserva = await apiFetch('/reservas/', {
        method: 'POST',
        body: JSON.stringify({
          cliente_id: cliente.id,
          tipo_quarto_id: tipoSelecionado.id,
          data_entrada: dataEntrada,
          data_saida: dataSaida,
        }),
      })
      setReservaCriada(reserva)
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      if (err.status === 409) {
        setSemDisponibilidade(true)
      } else {
        setErroConfirm(err.message)
      }
    } finally {
      setConfirmando(false)
    }
  }

  async function handleListaEspera() {
    if (!tipoSelecionado || !cliente) return
    setErroConfirm('')
    setConfirmando(true)
    try {
      const reserva = await apiFetch('/reservas/lista-espera/', {
        method: 'POST',
        body: JSON.stringify({
          cliente_id: cliente.id,
          tipo_quarto_id: tipoSelecionado.id,
          data_entrada: dataEntrada,
          data_saida: dataSaida,
        }),
      })
      setReservaCriada(reserva)
      setSemDisponibilidade(false)
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroConfirm(err.message)
    } finally {
      setConfirmando(false)
    }
  }

  function novaReserva() {
    setReservaCriada(null)
    setTipoSelecionado(null)
    setCliente(null)
    setModoCliente('search')
    setErroConfirm('')
    setSemDisponibilidade(false)
  }

  const dias = calcularDias(dataEntrada, dataSaida)
  const valorEstimado = tipoSelecionado ? dias * Number(tipoSelecionado.precoBaseDiaria) : 0
  const dataMinSaida = dataEntrada
    ? new Date(new Date(dataEntrada).getTime() + 86400000).toISOString().split('T')[0]
    : ''

  return (
    <div className="reservas-page">
      <h1 className="page-title">Criar Reserva / Consultar Disponibilidade</h1>

      {/* ── Formulário de busca ── */}
      <form className="busca-form" onSubmit={handleBuscar}>
        <div className="busca-form__campos">
          <div className="form-field">
            <label className="form-label" htmlFor="dataEntrada">Data entrada</label>
            <input id="dataEntrada" type="date" className="form-input"
              value={dataEntrada} min={hoje}
              onChange={e => {
                setDataEntrada(e.target.value)
                if (dataSaida <= e.target.value) setDataSaida('')
                setSemDisponibilidade(false)
              }}
              required />
          </div>
          <div className="form-field">
            <label className="form-label" htmlFor="dataSaida">Data saída</label>
            <input id="dataSaida" type="date" className="form-input"
              value={dataSaida} min={dataMinSaida}
              onChange={e => { setDataSaida(e.target.value); setSemDisponibilidade(false) }}
              required />
          </div>
          <div className="form-field">
            <label className="form-label" htmlFor="nPessoas">N° pessoas</label>
            <input id="nPessoas" type="number" className="form-input form-input--sm"
              value={nPessoas} min={1} max={20}
              onChange={e => setNPessoas(Number(e.target.value))} />
          </div>
        </div>
        <button type="submit" className="btn btn--primary busca-form__btn"
          disabled={buscando || !dataEntrada || !dataSaida}>
          {buscando ? 'Buscando…' : 'Buscar'}
        </button>
      </form>

      {erroBusca && <p className="page-erro" role="alert">{erroBusca}</p>}

      {/* ── Resultados ── */}
      {buscado && !erroBusca && (
        <div className="reservas-resultado">

          {/* Coluna esquerda */}
          <section className="tipos-panel">
            <div className="panel-header">
              <h2 className="panel-titulo">Quartos Disponíveis</h2>
              <button type="button" className="btn-cancelar" onClick={handleCancelar}>
                ← Cancelar
              </button>
            </div>
            {tipos.length === 0 ? (
              <p className="panel-vazio">Nenhum tipo de quarto encontrado para {nPessoas} pessoa(s).</p>
            ) : (
              <div className="tipos-lista">
                {tipos.map(tipo => (
                  <TipoCard
                    key={tipo.id}
                    tipo={tipo}
                    quartosPorTipo={quartosPorTipo}
                    selecionado={tipoSelecionado?.id === tipo.id}
                    onClick={handleSelecionarTipo}
                  />
                ))}
              </div>
            )}
          </section>

          {/* Coluna direita: painel da reserva */}
          {tipoSelecionado && (
            <section className="reserva-panel">
              <h2 className="panel-titulo">Reserva</h2>
              {checkandoDisp ? (
                <div className="reserva-checando" role="status" aria-live="polite">
                  <span className="busca-cliente__spinner" style={{ display: 'inline-block', marginRight: 8 }} aria-hidden="true" />
                  Verificando disponibilidade…
                </div>
              ) : reservaCriada ? (
                /* ── Sucesso ── */
                <div className={`reserva-sucesso${reservaCriada.status === 'LISTA_ESPERA' ? ' reserva-sucesso--espera' : ''}`}>
                  <p className="reserva-sucesso__icone" aria-hidden="true">
                    {reservaCriada.status === 'LISTA_ESPERA' ? '⏳' : '✓'}
                  </p>
                  <p className="reserva-sucesso__titulo">
                    {reservaCriada.status === 'LISTA_ESPERA'
                      ? 'Adicionado à lista de espera!'
                      : 'Reserva confirmada!'}
                  </p>
                  {reservaCriada.status === 'LISTA_ESPERA' && (
                    <p className="reserva-sucesso__desc">
                      O cliente será contactado quando um quarto ficar disponível.
                    </p>
                  )}
                  <dl className="reserva-resumo">
                    <div><dt>Nº reserva</dt><dd>#{reservaCriada.id}</dd></div>
                    <div><dt>Cliente</dt><dd>{cliente.nome}</dd></div>
                    <div><dt>Tipo</dt><dd>{tipoSelecionado.nome}</dd></div>
                    <div><dt>Entrada</dt><dd>{fmtData(dataEntrada)}</dd></div>
                    <div><dt>Saída</dt><dd>{fmtData(dataSaida)}</dd></div>
                    <div><dt>Valor previsto</dt><dd>{formatBRL(reservaCriada.valor_total_previsto)}</dd></div>
                  </dl>
                  <button className="btn btn--primary" style={{ marginTop: 16 }} onClick={novaReserva}>
                    Nova reserva
                  </button>
                </div>
              ) : (
                <>
                  <dl className="reserva-resumo">
                    <div><dt>Entrada</dt><dd>{fmtData(dataEntrada)}</dd></div>
                    <div><dt>Saída</dt><dd>{fmtData(dataSaida)}</dd></div>
                    <div><dt>Tipo Quarto</dt><dd>{tipoSelecionado.nome}</dd></div>
                    {dias > 0 && <div><dt>Diárias</dt><dd>{dias}</dd></div>}
                  </dl>

                  <div className="cliente-section">
                    {modoCliente === 'search' ? (
                      <>
                        <BuscaCliente onSelecionar={setCliente} />
                        {cliente && (
                          <div className="cliente-selecionado">
                            <span>👤 {cliente.nome}</span>
                            <button type="button" className="btn-link" onClick={() => setCliente(null)}>
                              Trocar
                            </button>
                          </div>
                        )}
                        <button type="button" className="btn btn--outline"
                          onClick={() => { setModoCliente('new'); setCliente(null) }}>
                          + Novo Cliente
                        </button>
                      </>
                    ) : (
                      <FormNovoCliente
                        onCriado={c => { setCliente(c); setModoCliente('search') }}
                        onCancelar={() => setModoCliente('search')}
                      />
                    )}
                  </div>

                  <div className="reserva-rodape">
                    <div className="valor-estimado">
                      <span className="valor-estimado__label">Valor estimado</span>
                      <span className="valor-estimado__valor">{formatBRL(valorEstimado)}</span>
                    </div>

                    {semDisponibilidade ? (
                      /* ── Estado sem disponibilidade (A3/E1) ── */
                      <div className="indisponivel">
                        <p className="indisponivel__msg">
                          Não há quartos disponíveis para o período selecionado.
                        </p>
                        <button type="button" className="btn btn--espera btn--full"
                          disabled={confirmando || !cliente} onClick={handleListaEspera}>
                          {confirmando ? 'Aguarde…' : '⏳ Adicionar à Lista de Espera'}
                        </button>
                        {!cliente && (
                          <p className="reserva-hint">Selecione ou cadastre um cliente para continuar.</p>
                        )}
                      </div>
                    ) : (
                      <>
                        {erroConfirm && <p className="form-erro" role="alert">{erroConfirm}</p>}
                        <button type="button" className="btn btn--primary btn--full"
                          disabled={confirmando || !cliente} onClick={handleConfirmar}>
                          {confirmando ? 'Confirmando…' : 'Confirmar Reserva'}
                        </button>
                        {!cliente && (
                          <p className="reserva-hint">Selecione ou cadastre um cliente para continuar.</p>
                        )}
                      </>
                    )}
                  </div>
                </>
              )}
            </section>
          )}
        </div>
      )}
    </div>
  )
}

export default Reservas
