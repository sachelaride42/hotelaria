import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Reservas from './pages/Reservas'
import Checkin from './pages/Checkin'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reservas" element={<Reservas />} />
          <Route path="/checkin" element={<Checkin />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
