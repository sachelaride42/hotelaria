import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { jsPDF } from 'jspdf'
import { apiFetch } from '../services/api'
import './Governanca.css'

const OCUPACAO_LABEL = { LIVRE: 'Livre', OCUPADO: 'Ocupado', MANUTENCAO: 'Manutenção' }
const LIMPEZA_LABEL  = { LIMPO: 'Limpo', SUJO: 'Sujo' }

function Governanca() {
  const [quartos, setQuartos]                   = useState([])
  const [tipos, setTipos]                       = useState({})
  const [filtro, setFiltro]                     = useState('')
  const [loading, setLoading]                   = useState(true)
  const [error, setError]                       = useState(null)
  const [atualizandoLimpezaId, setAtualizandoLimpezaId]   = useState(null)
  const [limparTodosLoading, setLimparTodosLoading] = useState(false)
  const [modalAberto, setModalAberto]           = useState(false)
  const [erroAcao, setErroAcao]                 = useState(null)
  const navigate = useNavigate()

  const quartosFiltrados = filtro === 'SUJO'
    ? quartos.filter(q => q.status_limpeza === 'SUJO')
    : quartos

  const quartosSujos = quartos.filter(q => q.status_limpeza === 'SUJO')

  useEffect(() => {
    Promise.all([
      apiFetch('/quartos/'),
      apiFetch('/tipos-quarto/').catch(() => []),
    ])
      .then(([quartosData, tiposData]) => {
        setQuartos(quartosData)
        const map = {}
        tiposData.forEach(t => { map[t.id] = t.nome })
        setTipos(map)
      })
      .catch(err => {
        if (err.status === 401) navigate('/login')
        else setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [navigate])

  async function atualizarLimpeza(quarto, novoStatus) {
    if (atualizandoLimpezaId !== null || limparTodosLoading) return
    setAtualizandoLimpezaId(quarto.id)
    setErroAcao(null)
    const endpoint = novoStatus === 'LIMPO'
      ? `/governanca/limpeza/${quarto.id}/concluir`
      : `/governanca/limpeza/${quarto.id}/solicitar`
    try {
      await apiFetch(endpoint, {
        method: 'PATCH',
        body: JSON.stringify({ versao: quarto.versao }),
      })
      setQuartos(prev =>
        prev.map(q =>
          q.id === quarto.id
            ? { ...q, status_limpeza: novoStatus, versao: q.versao + 1 }
            : q
        )
      )
    } catch (err) {
      if (err.status === 401) navigate('/login')
      else if (err.status === 409) setErroAcao('Conflito de versão. Recarregue a página.')
      else if (err.status === 400) setErroAcao(`Quarto ${quarto.numero}: ${err.message}`)
      else setErroAcao(err.message)
    } finally {
      setAtualizandoLimpezaId(null)
    }
  }

  async function limparTodos() {
    setModalAberto(false)
    setLimparTodosLoading(true)
    setErroAcao(null)
    const sujos = quartos.filter(q => q.status_limpeza === 'SUJO')
    const erros = []
    for (const quarto of sujos) {
      try {
        await apiFetch(`/governanca/limpeza/${quarto.id}/concluir`, {
          method: 'PATCH',
          body: JSON.stringify({ versao: quarto.versao }),
        })
        setQuartos(prev =>
          prev.map(q =>
            q.id === quarto.id
              ? { ...q, status_limpeza: 'LIMPO', versao: q.versao + 1 }
              : q
          )
        )
      } catch (err) {
        if (err.status === 401) { navigate('/login'); return }
        if (err.status === 400) continue
        erros.push(`Quarto ${quarto.numero}: ${err.message}`)
      }
    }
    if (erros.length > 0) setErroAcao(`${erros.length} quarto(s) com erro: ${erros.join('; ')}`)
    setLimparTodosLoading(false)
  }

  function gerarRelatorio() {
    const sujos = quartos.filter(q => q.status_limpeza === 'SUJO')
    const agora = new Date().toLocaleString('pt-BR')
    const doc = new jsPDF()

    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.text('Relatório de Limpeza', 14, 20)

    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(100)
    doc.text(`Gerado em: ${agora}`, 14, 28)
    doc.text(`Total de quartos com pendência: ${sujos.length}`, 14, 34)
    doc.setTextColor(0)

    let y = 46
    doc.setFillColor(240, 240, 240)
    doc.rect(14, y - 5, 182, 8, 'F')
    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.text('Quarto', 16, y)
    doc.text('Andar', 50, y)
    doc.text('Tipo', 72, y)
    doc.text('Status Hospedagem', 130, y)
    y += 10

    doc.setFont('helvetica', 'normal')
    for (const q of sujos) {
      if (y > 270) { doc.addPage(); y = 20 }
      doc.text(String(q.numero), 16, y)
      doc.text(`${q.andar}º`, 50, y)
      doc.text(tipos[q.tipo_quarto_id] ?? '—', 72, y)
      doc.text(OCUPACAO_LABEL[q.status_ocupacao] ?? q.status_ocupacao, 130, y)
      y += 8
    }

    doc.save('relatorio-limpeza.pdf')
  }

  return (
    <div className="gov-page">
      <div className="gov-header">
        <h1 className="gov-title">Governança</h1>
      </div>

      {loading && (
        <div className="gov-feedback" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando quartos…</p>
        </div>
      )}

      {error && (
        <div className="gov-feedback gov-feedback--error" role="alert">
          <p>Não foi possível carregar os quartos.</p>
          <p className="gov-error-detail">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          <div
            className="gov-filters"
            role="group"
            aria-label="Filtrar por status de limpeza"
          >
            <button
              className={`filter-btn${filtro === '' ? ' filter-btn--active' : ''}`}
              onClick={() => setFiltro('')}
              aria-pressed={filtro === ''}
            >
              Todos
            </button>
            <button
              className={`filter-btn${filtro === 'SUJO' ? ' filter-btn--active' : ''}`}
              onClick={() => setFiltro('SUJO')}
              aria-pressed={filtro === 'SUJO'}
            >
              Sujos (Prioridade)
              {quartosSujos.length > 0 && (
                <span className="gov-filter-count" aria-label={`${quartosSujos.length} quartos sujos`}>
                  {quartosSujos.length}
                </span>
              )}
            </button>
          </div>

          {erroAcao && (
            <p className="gov-erro-acao" role="alert">{erroAcao}</p>
          )}

          <div className="gov-toolbar">
            <button
              className="btn btn--primary"
              disabled={quartosSujos.length === 0 || limparTodosLoading}
              onClick={() => setModalAberto(true)}
              aria-busy={limparTodosLoading}
            >
              {limparTodosLoading
                ? <><span className="btn-spinner" aria-hidden="true" /> Limpando…</>
                : 'Limpar Todos'
              }
            </button>
          </div>

          {quartosFiltrados.length === 0 && (
            <div className="gov-feedback" role="status" aria-live="polite">
              <p>Nenhum quarto com pendência de limpeza imediata.</p>
            </div>
          )}

          {quartosFiltrados.length > 0 && (
            <div className="table-wrapper">
              <table className="gov-table" aria-label="Quartos – status de limpeza">
                <thead>
                  <tr>
                    <th scope="col">Quarto</th>
                    <th scope="col">Tipo</th>
                    <th scope="col">Status Hospedagem</th>
                    <th scope="col">Status Limpeza</th>
                    <th scope="col">Alterar Limpeza</th>
                  </tr>
                </thead>
                <tbody>
                  {quartosFiltrados.map(quarto => (
                    <tr key={quarto.id}>
                      <td>{quarto.numero}</td>
                      <td>{tipos[quarto.tipo_quarto_id] ?? `Tipo ${quarto.tipo_quarto_id}`}</td>
                      <td>
                        <span className={`badge badge--${quarto.status_ocupacao.toLowerCase()}`}>
                          {OCUPACAO_LABEL[quarto.status_ocupacao]}
                        </span>
                      </td>
                      <td>
                        <span className={`gov-limpeza gov-limpeza--${quarto.status_limpeza.toLowerCase()}`}>
                          {LIMPEZA_LABEL[quarto.status_limpeza]}
                        </span>
                      </td>
                      <td>
                        {atualizandoLimpezaId === quarto.id
                          ? <span className="cell-spinner" aria-hidden="true" />
                          : (
                            <select
                              className="gov-select"
                              value={quarto.status_limpeza}
                              disabled={atualizandoLimpezaId !== null || limparTodosLoading}
                              onChange={e => atualizarLimpeza(quarto, e.target.value)}
                              aria-label={`Alterar status de limpeza do quarto ${quarto.numero}`}
                            >
                              <option value="LIMPO">Limpo</option>
                              <option value="SUJO">Sujo</option>
                            </select>
                          )
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="gov-actions-bottom">
            <button className="btn btn--outline" onClick={gerarRelatorio}>
              Gerar Relatório de Limpeza
            </button>
          </div>
        </>
      )}

      {modalAberto && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar limpeza em massa"
          onClick={e => { if (e.target === e.currentTarget) setModalAberto(false) }}
        >
          <div className="modal modal--pequeno">
            <div className="modal__header">
              <h2 className="modal__titulo">Limpar todos os quartos</h2>
              <button
                className="modal__fechar"
                onClick={() => setModalAberto(false)}
                aria-label="Fechar"
              >
                ✕
              </button>
            </div>
            <p className="modal__corpo">
              Deseja marcar todos os <strong>{quartosSujos.length}</strong> quarto(s) sujo(s)
              como limpos?
            </p>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setModalAberto(false)}>
                Cancelar
              </button>
              <button className="btn btn--primary" onClick={limparTodos}>
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Governanca
