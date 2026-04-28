import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Reservas from './pages/Reservas'
import Checkin from './pages/Checkin'
import Clientes from './pages/Clientes'
import HospedagemDetalhe from './pages/HospedagemDetalhe'
import QuartoDetalhe from './pages/QuartoDetalhe'
import Extrato from './pages/Extrato'
import Checkout from './pages/Checkout'
import GradeOcupados from './pages/GradeOcupados'
import Governanca from './pages/Governanca'
import QuartosAdmin from './pages/QuartosAdmin'
import ReservasAdmin from './pages/ReservasAdmin'
import Produtos from './pages/Produtos'
import TiposQuartoAdmin from './pages/TiposQuartoAdmin'
import UsuariosAdmin from './pages/UsuariosAdmin'
import Perfil from './pages/Perfil'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reservas" element={<Reservas />} />
          <Route path="/checkin" element={<Checkin />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/hospedagens" element={<GradeOcupados titulo="Hospedagens Ativas" destino="hospedagem" />} />
          <Route path="/lancamentos" element={<GradeOcupados titulo="Lançar Produtos / Serviços" destino="extrato" />} />
          <Route path="/checkout" element={<GradeOcupados titulo="Checkout / Caixa" destino="checkout" />} />
          <Route path="/hospedagem/:hospedagemId" element={<HospedagemDetalhe />} />
          <Route path="/hospedagem/:hospedagemId/extrato" element={<Extrato />} />
          <Route path="/checkout/:hospedagemId" element={<Checkout />} />
          <Route path="/quarto/:quartoId" element={<QuartoDetalhe />} />
          <Route path="/governanca" element={<Governanca />} />
          <Route path="/reservas-admin" element={<ReservasAdmin />} />
          <Route path="/quartos-admin" element={<QuartosAdmin />} />
          <Route path="/tipos-quarto-admin" element={<TiposQuartoAdmin />} />
          <Route path="/produtos" element={<Produtos />} />
          <Route path="/usuarios-admin" element={<UsuariosAdmin />} />
          <Route path="/perfil" element={<Perfil />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
