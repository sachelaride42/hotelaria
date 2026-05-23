import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiFetch } from '../services/api'
import './HospedagemHospedes.css'
import '../utils/masks'
import { maskTelefone } from '../utils/masks'

function InfoRow({ label, value }) {
  return (
    <div className="hh-row">
      <dt>{label}</dt>
      <dd>{value ?? <span className="hh-vazio">—</span>}</dd>
    </div>
  )
}

function formatCPF(cpf) {
  if (!cpf) return null
  const digits = cpf.replace(/\D/g, '')
  if (digits.length !== 11) return cpf
  return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
}

export default function HospedagemHospedes() {
  const { hospedagemId } = useParams()
  const navigate = useNavigate()

  const [cliente, setCliente] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const hosp = await apiFetch(`/hospedagens/${hospedagemId}`)
        const cli = await apiFetch(`/clientes/${hosp.cliente_id}`)
        setCliente(cli)
      } catch (err) {
        if (err.status === 401) navigate('/login')
        else setError(err.message ?? 'Falha ao carregar dados do hóspede.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [hospedagemId, navigate])

  if (loading) {
    return (
      <div className="hh-feedback" role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p>Carregando hóspede…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="hh-feedback hh-feedback--error" role="alert">
        <p>{error}</p>
        <button className="hh-btn-link" onClick={() => navigate(-1)}>← Voltar</button>
      </div>
    )
  }

  return (
    <div className="hh-page">
      <Link className="hh-voltar" to={`/hospedagem/${hospedagemId}`}>← Voltar</Link>

      <h1>Hóspede</h1>

      <section className="hh-card" aria-label="Dados do hóspede">
        <h2>Hóspede Principal</h2>
        <dl className="hh-lista">
          <InfoRow label="Nome" value={cliente.nome} />
          <InfoRow label="CPF" value={formatCPF(cliente.cpf)} />
          <InfoRow label="Telefone" value={maskTelefone(cliente.telefone)} />
          <InfoRow label="E-mail" value={cliente.email} />
        </dl>
      </section>
    </div>
  )
}
