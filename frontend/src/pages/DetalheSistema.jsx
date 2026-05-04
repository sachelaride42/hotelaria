import { useNavigate } from 'react-router-dom'
import './DetalheSistema.css'

const FUNCIONALIDADES = [
  'Dashboard com grade de quartos e status em tempo real',
  'Check-in de hóspedes',
  'Gestão de reservas',
  'Controle de hospedagens ativas com grade de ocupação',
  'Lançamento de produtos e serviços por hospedagem',
  'Extrato financeiro por hospedagem',
  'Checkout e fechamento de conta',
  'Governança: controle e atualização do status de limpeza dos quartos',
  'Cadastro e gestão de clientes',
  'Cadastro e gestão de quartos',
  'Cadastro e gestão de tipos de quarto',
  'Cadastro e gestão de produtos e serviços',
  'Gestão de usuários (recepcionistas e gerentes)',
  'Perfil de usuário autenticado',
]

const SUGESTOES = [
  'Cadastro completo de hóspedes com dados legalmente exigidos',
  'Auditabilidade econômico-financeira com registros imutáveis',
  'Conformidade e auditabilidade segundo a LGPD',
  'Rastreabilidade de operações críticas por funcionário responsável',
  'Fechamento de caixa por turno vinculado ao operador',
  'Relatório de receita por período com exportação',
  'Integração com meios de pagamento eletrônico (cartão e PIX)',
  'Emissão de nota fiscal eletrônica (NF-e) no checkout',
  'Controle de estoque de produtos com alertas de reposição',
  'Controle de manutenção preventiva e corretiva de quartos',
  'Painel de indicadores gerenciais (taxa de ocupação, RevPAR, ticket médio)',
  'Integração com plataformas de reserva online (Booking.com, Airbnb)',
  'Portal de autoatendimento para hóspedes',
  'Backup automático e plano de recuperação de dados',
]

export default function DetalheSistema() {
  const navigate = useNavigate()

  return (
    <div className="detalhe-sistema-page">
      <div className="detalhe-sistema-header">
        <button className="btn-voltar" onClick={() => navigate(-1)}>← Voltar</button>
        <h1>Detalhes do Sistema</h1>
      </div>

      <section className="detalhe-sistema-section">
        <h2>Funcionalidades</h2>
        <ul className="detalhe-sistema-list">
          {FUNCIONALIDADES.map(item => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="detalhe-sistema-section">
        <h2>Sugestões para futuros aprimoramentos</h2>
        <p className="detalhe-sistema-intro">
          O atual sistema já cumpre todas as funcionalidades para o escopo de trabalho em que
          foi definido. Porém, ainda há espaço para aprimoramentos se o objetivo for tornar o
          sistema mais robusto.
        </p>
        <ul className="detalhe-sistema-list">
          {SUGESTOES.map(item => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  )
}
