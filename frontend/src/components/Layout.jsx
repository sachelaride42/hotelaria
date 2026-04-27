import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import './Layout.css'

const menuOperacional = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/checkin', label: 'Check-in / Recepção' },
  { to: '/reservas', label: 'Reservas / Consultar Disponibilidade' },
  { to: '/hospedagens', label: 'Hospedagens ativas' },
  { to: '/lancamentos', label: 'Lançar Produtos / Serviços' },
  { to: '/checkout', label: 'Checkout / Caixa' },
]

const menuServicos = [
  { to: '/governanca', label: 'Governança' },
]

const menuCadastro = [
  { to: '/clientes', label: 'Clientes' },
  { to: '/quartos-admin', label: 'Quartos' },
  { to: '/produtos', label: 'Produtos / Serviços' },
]

function SidebarSection({ label, links }) {
  return (
    <div className="sidebar-section">
      <p className="sidebar-section__label">{label}</p>
      {links.map(({ to, label: linkLabel, exact }) => (
        <NavLink
          key={to}
          to={to}
          end={exact}
          className={({ isActive }) =>
            'sidebar-link' + (isActive ? ' sidebar-link--active' : '')
          }
        >
          {linkLabel}
        </NavLink>
      ))}
    </div>
  )
}

function Layout() {
  const navigate = useNavigate()

  function handleSair() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="layout">
      <header className="topbar">
        <nav className="topbar-nav" aria-label="Navegação principal">
          <button className="topbar-btn topbar-btn--active" onClick={() => navigate('/')}>HOTEL</button>
          <button className="topbar-btn" onClick={() => navigate('/perfil')}>Perfil</button>
          <button className="topbar-btn" onClick={handleSair}>Sair</button>
        </nav>
      </header>

      <div className="layout-body">
        <aside className="sidebar" aria-label="Menu lateral">
          <p className="sidebar-title">Menu</p>
          <SidebarSection label="Operacional" links={menuOperacional} />
          <SidebarSection label="Serviços" links={menuServicos} />
          <SidebarSection label="Cadastro" links={menuCadastro} />
        </aside>

        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
