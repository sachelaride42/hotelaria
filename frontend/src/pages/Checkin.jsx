import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, getUserRole } from '../services/api'
import { maskCPF, maskTelefone, stripMask } from '../utils/masks'
import './Checkin.css'

/* ── Helpers ── */
function formatBRL(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function fmtData(iso) {
  if (!iso) return '—'
  return new Date(iso + 'T12:00').toLocaleDateString('pt-BR')
}

function calcularDias(dataEntrada, dataSaida) {
  if (!dataEntrada || !dataSaida) return 0
  return Math.max(0, Math.round((new Date(dataSaida) - new Date(dataEntrada)) / 86400000))
}

/* ── BuscaCliente autocomplete (walk-in) ── */
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
        <span className="busca-cliente__icon" aria-hidden="true">&#128269;</span>
        <input
          type="text"
          className="form-input"
          placeholder="Nome ou CPF do hóspede…"
          value={query}
          onChange={handleChange}
          onFocus={() => resultados.length > 0 && setAberto(true)}
          aria-label="Pesquisar hóspede por nome ou CPF"
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
        <p className="busca-cliente__vazio">Nenhum hóspede encontrado.</p>
      )}
    </div>
  )
}

/* ── FormNovoCliente ── */
function FormNovoCliente({ onCriado, onCancelar, clienteInicial }) {
  const [form, setForm] = useState({
    nome: clienteInicial?.nome ?? '',
    telefone: clienteInicial?.telefone ?? '',
    cpf: clienteInicial?.cpf ? maskCPF(clienteInicial.cpf) : '',
    email: clienteInicial?.email ?? '',
  })
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')

  const editando = Boolean(clienteInicial?.id)

  function handleTelefone(e) {
    const v = e.target.value
    setForm(f => ({ ...f, telefone: v.startsWith('+') ? v : maskTelefone(v) }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErro('')
    setSalvando(true)
    try {
      const telRaw = form.telefone.startsWith('+') ? form.telefone.trim() : stripMask(form.telefone)
      const payload = { nome: form.nome.trim(), telefone: telRaw }
      if (form.cpf.trim()) payload.cpf = stripMask(form.cpf)
      if (form.email.trim()) payload.email = form.email.trim()
      const cliente = editando
        ? await apiFetch(`/clientes/${clienteInicial.id}`, { method: 'PUT', body: JSON.stringify(payload) })
        : await apiFetch('/clientes/', { method: 'POST', body: JSON.stringify(payload) })
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
          <input className="form-input" required value={form.nome}
            onChange={e => setForm(f => ({ ...f, nome: e.target.value }))}
            placeholder="Nome completo" />
        </div>
        <div className="form-field">
          <label className="form-label">
            Telefone *
            {telInternacional && <span className="form-label__hint"> — internacional</span>}
          </label>
          <input className="form-input" required value={form.telefone}
            onChange={handleTelefone} placeholder="(11) 99999-9999" />
        </div>
        <div className="form-field">
          <label className="form-label">CPF</label>
          <input className="form-input" value={form.cpf} inputMode="numeric"
            onChange={e => setForm(f => ({ ...f, cpf: maskCPF(e.target.value) }))}
            placeholder="000.000.000-00" />
        </div>
        <div className="form-field">
          <label className="form-label">E-mail</label>
          <input className="form-input" type="email" value={form.email}
            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            placeholder="email@exemplo.com" />
        </div>
      </div>
      {erro && <p className="form-erro" role="alert">{erro}</p>}
      <div className="form-novo-cliente__actions">
        <button type="button" className="btn btn--ghost" onClick={onCancelar}>Cancelar</button>
        <button type="submit" className="btn btn--primary"
          disabled={salvando || !form.nome || !form.telefone}>
          {salvando ? 'Salvando…' : editando ? 'Salvar alterações' : 'Salvar hóspede'}
        </button>
      </div>
    </form>
  )
}

/* ── Página principal ── */
export default function Checkin() {
  const navigate = useNavigate()
  const hoje = new Date().toISOString().split('T')[0]

  /* ── Estado global da máquina ── */
  const [etapa, setEtapa] = useState('busca') // 'busca' | 'confirmacao' | 'sucesso'
  const [modoWalkin, setModoWalkin] = useState(false)

  /* ── Etapa 1: busca ── */
  const [buscaTermo, setBuscaTermo] = useState('')
  const [buscando, setBuscando] = useState(false)
  const [resultados, setResultados] = useState([]) // [{reserva, cliente}]
  const [erroBusca, setErroBusca] = useState('')
  const [buscaRealizada, setBuscaRealizada] = useState(false)

  /* ── Dados carregados no mount ── */
  const [tiposMap, setTiposMap] = useState({}) // id → {nome, precoBaseDiaria}
  const [todosOsTipos, setTodosOsTipos] = useState([])

  /* ── Etapa 2: confirmação ── */
  const [reservaSelecionada, setReservaSelecionada] = useState(null)
  const [clienteEtapa2, setClienteEtapa2] = useState(null)
  const [modoCliente, setModoCliente] = useState('search') // 'selecionado' | 'search' | 'novo'
  const [modoEditarCliente, setModoEditarCliente] = useState(false)
  const [tipoSelecionado, setTipoSelecionado] = useState(null)
  const [quartos, setQuartos] = useState([])
  const [quartoSelecionado, setQuartoSelecionado] = useState(null)
  const [dataCheckout, setDataCheckout] = useState('')
  const [loadingQuartos, setLoadingQuartos] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const [erroConfirm, setErroConfirm] = useState('')

  /* ── UC5: Alteração de preço da diária ── */
  const [modoEditarPreco, setModoEditarPreco] = useState(false)
  const [valorDiariaInput, setValorDiariaInput] = useState('')  // campo de edição
  const [valorDiariaCustom, setValorDiariaCustom] = useState(null) // null = usa preço do tipo
  const [erroPreco, setErroPreco] = useState('')

  /* ── Etapa 3: sucesso ── */
  const [hospedagemCriada, setHospedagemCriada] = useState(null)

  /* ── Carrega tipos de quarto no mount ── */
  useEffect(() => {
    apiFetch('/tipos-quarto/')
      .then(data => {
        const map = {}
        data.forEach(t => { map[t.id] = t })
        setTiposMap(map)
        setTodosOsTipos(data)
      })
      .catch(() => {})
  }, [])

  /* ── Carrega quartos quando tipo é selecionado na etapa 2 ── */
  useEffect(() => {
    if (!tipoSelecionado) { setQuartos([]); setQuartoSelecionado(null); return }
    setLoadingQuartos(true)
    setQuartoSelecionado(null)
    // Resetar preço customizado ao trocar de tipo
    setValorDiariaCustom(null)
    setModoEditarPreco(false)
    setErroPreco('')
    apiFetch(`/quartos/?tipo_quarto_id=${tipoSelecionado.id}&status_ocupacao=LIVRE&status_limpeza=LIMPO`)
      .then(data => setQuartos(data))
      .catch(() => setQuartos([]))
      .finally(() => setLoadingQuartos(false))
  }, [tipoSelecionado])

  /* ── Handlers etapa 1 ── */
  async function handleBuscar(e) {
    e.preventDefault()
    const termo = buscaTermo.trim()
    if (!termo) return
    setErroBusca('')
    setBuscando(true)
    setBuscaRealizada(false)
    setResultados([])
    try {
      const ehCPF = /^\d/.test(termo)
      const valor = ehCPF ? stripMask(termo) : termo
      const campo = ehCPF ? `cpf=${encodeURIComponent(valor)}` : `nome=${encodeURIComponent(valor)}`
      const clientes = await apiFetch(`/clientes/?${campo}`)
      if (clientes.length === 0) {
        setResultados([])
        setBuscaRealizada(true)
        return
      }
      const todas = await Promise.all(
        clientes.map(c =>
          apiFetch(`/reservas/?cliente_id=${c.id}&status=CONFIRMADA`)
            .then(reservas => reservas.map(r => ({ reserva: r, cliente: c })))
            .catch(() => [])
        )
      )
      setResultados(todas.flat())
      setBuscaRealizada(true)
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroBusca(err.message)
    } finally {
      setBuscando(false)
    }
  }

  function iniciarCheckinComReserva(reserva, cliente) {
    const tipo = tiposMap[reserva.tipo_quarto_id]
    setReservaSelecionada(reserva)
    setClienteEtapa2(cliente)
    setModoCliente('selecionado')
    setModoEditarCliente(false)
    setTipoSelecionado(tipo ?? null)
    setDataCheckout(reserva.data_saida)
    setErroConfirm('')
    setEtapa('confirmacao')
    setModoWalkin(false)
  }

  function iniciarCheckinWalkin() {
    setReservaSelecionada(null)
    setClienteEtapa2(null)
    setModoCliente('search')
    setModoEditarCliente(false)
    setTipoSelecionado(null)
    setDataCheckout('')
    setErroConfirm('')
    setModoWalkin(true)
    setEtapa('confirmacao')
  }

  /* ── Handlers etapa 2 ── */
  function handleSelecionarTipo(tipo) {
    setTipoSelecionado(tipo)
    setErroConfirm('')
  }

  function handleAbrirEditarPreco() {
    setValorDiariaInput(
      valorDiariaCustom !== null
        ? String(valorDiariaCustom)
        : String(Number(tipoAtual?.precoBaseDiaria ?? 0))
    )
    setErroPreco('')
    setModoEditarPreco(true)
  }

  function handleSalvarPreco() {
    const v = Number(valorDiariaInput.replace(',', '.'))
    if (isNaN(v) || v <= 0) {
      setErroPreco('Valor inválido. Insira apenas números positivos.')
      return
    }
    setValorDiariaCustom(v)
    setModoEditarPreco(false)
    setErroPreco('')
  }

  function handleCancelarEditarPreco() {
    setModoEditarPreco(false)
    setErroPreco('')
  }

  function handleSelecionarQuarto(e) {
    const id = Number(e.target.value)
    setQuartoSelecionado(quartos.find(q => q.id === id) ?? null)
  }

  async function handleFinalizar() {
    if (!clienteEtapa2 || !quartoSelecionado || !dataCheckout) return
    if (reservaSelecionada && reservaSelecionada.data_entrada !== hoje) {
      setErroConfirm('O check-in só pode ser realizado na data de entrada da reserva.')
      return
    }
    setErroConfirm('')
    setConfirmando(true)
    try {
      const payload = {
        cliente_id: clienteEtapa2.id,
        quarto_id: quartoSelecionado.id,
        reserva_id: reservaSelecionada?.id ?? null,
        data_checkout_previsto: `${dataCheckout}T14:00:00`,
        versao_quarto: quartoSelecionado.versao,
        ...(valorDiariaCustom !== null && { valor_diaria_negociado: valorDiariaCustom }),
      }
      const hosp = await apiFetch('/hospedagens/checkin', { method: 'POST', body: JSON.stringify(payload) })
      setHospedagemCriada(hosp)
      setEtapa('sucesso')
    } catch (err) {
      if (err.status === 401) { navigate('/login'); return }
      setErroConfirm(err.message)
    } finally {
      setConfirmando(false)
    }
  }

  function resetar() {
    setEtapa('busca')
    setModoWalkin(false)
    setBuscaTermo('')
    setResultados([])
    setBuscaRealizada(false)
    setErroBusca('')
    setReservaSelecionada(null)
    setClienteEtapa2(null)
    setModoCliente('search')
    setModoEditarCliente(false)
    setTipoSelecionado(null)
    setQuartos([])
    setQuartoSelecionado(null)
    setDataCheckout('')
    setErroConfirm('')
    setHospedagemCriada(null)
    setValorDiariaCustom(null)
    setModoEditarPreco(false)
    setValorDiariaInput('')
    setErroPreco('')
  }

  const tipoAtual = tipoSelecionado ?? (reservaSelecionada ? tiposMap[reservaSelecionada.tipo_quarto_id] : null)
  const podeFinalizarCheckin = clienteEtapa2 && quartoSelecionado && dataCheckout
  const isGerente = getUserRole() === 'GERENTE'
  const valorDiariaEfetivo = valorDiariaCustom !== null
    ? valorDiariaCustom
    : (tipoAtual ? Number(tipoAtual.precoBaseDiaria) : null)
  const diasEstadia = calcularDias(
    reservaSelecionada?.data_entrada ?? hoje,
    dataCheckout
  )
  const valorTotalEstimado = valorDiariaEfetivo !== null && diasEstadia > 0
    ? valorDiariaEfetivo * diasEstadia
    : null

  /* ═══════════════════════════════════════════════
     RENDER
  ═══════════════════════════════════════════════ */

  /* ── Sucesso ── */
  if (etapa === 'sucesso') {
    return (
      <div className="checkin-page">
        <h1 className="page-title">Realizar Check-in</h1>
        <div className="sucesso-checkin" role="status">
          <p className="sucesso-checkin__icone" aria-hidden="true">&#10003;</p>
          <p className="sucesso-checkin__titulo">Check-in realizado com sucesso!</p>
          <dl className="sucesso-checkin__resumo">
            <div><dt>Hóspede</dt><dd>{clienteEtapa2?.nome}</dd></div>
            <div><dt>Quarto</dt><dd>{quartoSelecionado?.numero}</dd></div>
            {tipoAtual && <div><dt>Tipo</dt><dd>{tipoAtual.nome}</dd></div>}
            <div><dt>Check-in</dt><dd>{new Date().toLocaleDateString('pt-BR')}</dd></div>
            <div><dt>Saída prevista</dt><dd>{fmtData(dataCheckout)}</dd></div>
            {hospedagemCriada && (
              <div><dt>Nº hospedagem</dt><dd>#{hospedagemCriada.id}</dd></div>
            )}
          </dl>
          <button className="btn btn--primary" onClick={resetar}>
            Novo Check-in
          </button>
        </div>
      </div>
    )
  }

  /* ── Etapa 2: confirmação ── */
  if (etapa === 'confirmacao') {
    return (
      <div className="checkin-page">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn-voltar" onClick={() => setEtapa('busca')} aria-label="Voltar para busca">
            &#8592; Voltar
          </button>
          <h1 className="page-title" style={{ margin: 0 }}>Realizar Check-in</h1>
        </div>

        {/* Grid duas colunas */}
        <div className="confirmacao-layout">

          {/* Dados do Hóspede */}
          <div className="confirmacao-panel">
            <p className="confirmacao-panel__titulo">Dados do Hóspede</p>

            {modoCliente === 'selecionado' && clienteEtapa2 && (
              <>
                {!modoEditarCliente ? (
                  <>
                    <div className="form-field">
                      <label className="form-label">Nome</label>
                      <input className="form-input" value={clienteEtapa2.nome} readOnly />
                    </div>
                    <div className="form-field">
                      <label className="form-label">CPF</label>
                      <input className="form-input"
                        value={clienteEtapa2.cpf ? maskCPF(clienteEtapa2.cpf) : '—'} readOnly />
                    </div>
                    <div className="form-field">
                      <label className="form-label">E-mail</label>
                      <input className="form-input" value={clienteEtapa2.email ?? '—'} readOnly />
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <button className="btn btn--ghost" onClick={() => setModoEditarCliente(true)}>
                        Editar Dados
                      </button>
                      {modoWalkin && (
                        <button className="btn-link" onClick={() => { setClienteEtapa2(null); setModoCliente('search') }}>
                          Trocar hóspede
                        </button>
                      )}
                    </div>
                  </>
                ) : (
                  <FormNovoCliente
                    clienteInicial={clienteEtapa2}
                    onCriado={c => { setClienteEtapa2(c); setModoEditarCliente(false) }}
                    onCancelar={() => setModoEditarCliente(false)}
                  />
                )}
              </>
            )}

            {modoCliente === 'search' && (
              <>
                <p className="confirmacao-panel__subtitulo">Pesquise o hóspede por nome ou CPF</p>
                <BuscaCliente onSelecionar={c => { setClienteEtapa2(c); setModoCliente('selecionado') }} />
                <button className="btn btn--ghost" style={{ alignSelf: 'flex-start' }}
                  onClick={() => setModoCliente('novo')}>
                  + Cadastrar novo hóspede
                </button>
              </>
            )}

            {modoCliente === 'novo' && (
              <FormNovoCliente
                onCriado={c => { setClienteEtapa2(c); setModoCliente('selecionado') }}
                onCancelar={() => setModoCliente('search')}
              />
            )}
          </div>

          {/* Alocação do Quarto */}
          <div className="confirmacao-panel">
            <p className="confirmacao-panel__titulo">Alocação do Quarto</p>

            {!modoWalkin && tipoAtual && (
              <p className="confirmacao-panel__subtitulo">
                Tipo Reservado: <strong>{tipoAtual.nome}</strong>
              </p>
            )}

            {modoWalkin && (
              <>
                <p className="confirmacao-panel__subtitulo">Selecione o tipo de quarto</p>
                <div className="tipo-selector" role="group" aria-label="Tipos de quarto">
                  {todosOsTipos.map(t => (
                    <button
                      key={t.id}
                      type="button"
                      className={`tipo-option${tipoSelecionado?.id === t.id ? ' tipo-option--ativo' : ''}`}
                      onClick={() => handleSelecionarTipo(t)}
                      aria-pressed={tipoSelecionado?.id === t.id}
                    >
                      <span className="tipo-option__nome">{t.nome}</span>
                      <span className="tipo-option__preco">{formatBRL(t.precoBaseDiaria)}/noite</span>
                    </button>
                  ))}
                </div>
              </>
            )}

            {tipoSelecionado && (
              <div className="form-field">
                <label className="form-label" htmlFor="quarto-select">
                  {loadingQuartos ? 'Carregando quartos…' : 'Selecione o Quarto'}
                </label>
                {quartos.length === 0 && !loadingQuartos ? (
                  <p className="form-erro" role="alert">
                    Nenhum quarto disponível (limpo e livre) para este tipo.
                  </p>
                ) : (
                  <select
                    id="quarto-select"
                    className="quarto-select"
                    value={quartoSelecionado?.id ?? ''}
                    onChange={handleSelecionarQuarto}
                    disabled={loadingQuartos}
                    aria-label="Quarto para alocação"
                  >
                    <option value="">-- Selecione o Quarto --</option>
                    {quartos.map(q => (
                      <option key={q.id} value={q.id}>
                        Quarto {q.numero} — Andar {q.andar}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Seção Valores */}
        <div className="valores-section">
          <p className="valores-section__titulo">Valores</p>
          <div className="valores-grid">
            {/* Valor da Diária — editável por Gerente (UC5) */}
            <div className="form-field">
              <div className="valores-diaria__header">
                <label className="form-label">Valor da Diária</label>
                {isGerente && tipoAtual && !modoEditarPreco && (
                  <button
                    type="button"
                    className="btn-link"
                    onClick={handleAbrirEditarPreco}
                    aria-label="Alterar preço da diária"
                  >
                    Alterar Preço
                  </button>
                )}
              </div>

              {modoEditarPreco ? (
                <div className="alterar-preco">
                  <div className="alterar-preco__row">
                    <input
                      className="form-input"
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={valorDiariaInput}
                      onChange={e => { setValorDiariaInput(e.target.value); setErroPreco('') }}
                      placeholder="Ex: 180.00"
                      aria-label="Novo valor da diária"
                      autoFocus
                    />
                    <button
                      type="button"
                      className="btn btn--primary"
                      onClick={handleSalvarPreco}
                    >
                      Aplicar
                    </button>
                    <button
                      type="button"
                      className="btn btn--ghost"
                      onClick={handleCancelarEditarPreco}
                    >
                      Cancelar
                    </button>
                  </div>
                  {tipoAtual && (
                    <p className="alterar-preco__original">
                      Preço original: {formatBRL(tipoAtual.precoBaseDiaria)}
                    </p>
                  )}
                  {erroPreco && (
                    <p className="form-erro" role="alert">{erroPreco}</p>
                  )}
                </div>
              ) : (
                <div className="alterar-preco__display">
                  <input
                    className="form-input"
                    value={valorDiariaEfetivo !== null ? formatBRL(valorDiariaEfetivo) : '—'}
                    readOnly
                    aria-label="Valor da diária"
                  />
                  {valorDiariaCustom !== null && tipoAtual && (
                    <p className="alterar-preco__badge">
                      Preço ajustado · original: {formatBRL(tipoAtual.precoBaseDiaria)}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="data-checkout">Previsão de Saída *</label>
              <input
                id="data-checkout"
                type="date"
                className="form-input"
                value={dataCheckout}
                min={hoje}
                onChange={e => setDataCheckout(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Total estimado */}
          {valorTotalEstimado !== null && (
            <div className="valores-total">
              <span className="valores-total__label">
                Total estimado ({diasEstadia} {diasEstadia === 1 ? 'diária' : 'diárias'})
              </span>
              <span className="valores-total__valor">{formatBRL(valorTotalEstimado)}</span>
            </div>
          )}

          {erroConfirm && (
            <p className="form-erro" role="alert">{erroConfirm}</p>
          )}

          <button
            className="btn btn--primary btn--full"
            onClick={handleFinalizar}
            disabled={confirmando || !podeFinalizarCheckin}
          >
            {confirmando ? 'Realizando check-in…' : 'Finalizar Check-in'}
          </button>
        </div>
      </div>
    )
  }

  /* ── Etapa 1: busca ── */
  return (
    <div className="checkin-page">
      <h1 className="page-title">Realizar Check-in</h1>

      {/* Buscar Reserva */}
      <section aria-labelledby="busca-titulo">
        <div className="busca-card">
          <p className="busca-card__label" id="busca-titulo">Buscar Reserva</p>
          <form onSubmit={handleBuscar}>
            <div className="busca-card__row">
              <div className="form-field" style={{ flex: 1 }}>
                <label className="form-label" htmlFor="busca-input">
                  Digite Nome, CPF ou Código
                </label>
                <div className="busca-card__input-wrap">
                  <span className="busca-card__icon" aria-hidden="true">&#128269;</span>
                  <input
                    id="busca-input"
                    type="text"
                    className="form-input"
                    placeholder="Pesquisar…"
                    value={buscaTermo}
                    onChange={e => {
                      let v = e.target.value
                      if (/^\d/.test(v) || v === '') v = maskCPF(v)
                      setBuscaTermo(v)
                    }}
                    aria-label="Pesquisar reserva por nome, CPF ou código"
                  />
                  {buscando && <span className="busca-card__spinner" aria-hidden="true" />}
                </div>
              </div>
              <div className="busca-card__actions">
                <button
                  type="submit"
                  className="btn btn--primary"
                  disabled={buscando || !buscaTermo.trim()}
                >
                  {buscando ? 'Buscando…' : 'Pesquisar Reserva'}
                </button>
                <button
                  type="button"
                  className="btn btn--outline"
                  onClick={iniciarCheckinWalkin}
                >
                  Check-in sem Reserva
                </button>
              </div>
            </div>
          </form>
        </div>
      </section>

      {erroBusca && <p className="busca-erro" role="alert">{erroBusca}</p>}

      {/* Resultados */}
      {buscaRealizada && (
        <section aria-labelledby="resultados-titulo">
          {resultados.length === 0 ? (
            <p className="reservas-vazia" role="status">
              Nenhuma reserva confirmada encontrada para este hóspede.
            </p>
          ) : (
            <div className="reservas-encontradas">
              <p className="reservas-encontradas__titulo" id="resultados-titulo">
                {resultados.length === 1 ? 'Reserva Encontrada' : `${resultados.length} Reservas Encontradas`}
              </p>
              {resultados.map(({ reserva, cliente }) => {
                const tipo = tiposMap[reserva.tipo_quarto_id]
                return (
                  <div className="reserva-card" key={reserva.id}>
                    <dl className="reserva-card__dados">
                      <div>
                        <dt>Cliente</dt>
                        <dd>{cliente.nome}</dd>
                      </div>
                      <div>
                        <dt>Entrada</dt>
                        <dd>{fmtData(reserva.data_entrada)}</dd>
                      </div>
                      <div>
                        <dt>Saída</dt>
                        <dd>{fmtData(reserva.data_saida)}</dd>
                      </div>
                      <div>
                        <dt>Tipo Quarto</dt>
                        <dd>{tipo?.nome ?? `ID ${reserva.tipo_quarto_id}`}</dd>
                      </div>
                      <div>
                        <dt>Nº Reserva</dt>
                        <dd>#{reserva.id}</dd>
                      </div>
                      <div>
                        <dt>Status</dt>
                        <dd><span className="reserva-card__status">{reserva.status}</span></dd>
                      </div>
                    </dl>
                    <button
                      className="btn btn--primary"
                      onClick={() => iniciarCheckinComReserva(reserva, cliente)}
                    >
                      Iniciar Check-in
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
