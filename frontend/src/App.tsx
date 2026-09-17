import { Route, Routes } from 'react-router-dom'
import Layout from './layout/Layout'
import DashboardPage from './pages/DashboardPage'
import SessionPage from './pages/SessionPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="session" element={<SessionPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
