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
          <Route path="/hospedagem/:hospedagemId" element={<HospedagemDetalhe />} />
          <Route path="/hospedagem/:hospedagemId/extrato" element={<Extrato />} />
          <Route path="/checkout/:hospedagemId" element={<Checkout />} />
          <Route path="/quarto/:quartoId" element={<QuartoDetalhe />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
