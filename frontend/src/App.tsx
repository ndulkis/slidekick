import { Route, Routes } from 'react-router-dom'
import Layout from './layout/Layout'
import DashboardPage from './pages/DashboardPage'
import OverlayPage from './pages/OverlayPage'
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
      {/* Outside Layout: the overlay must not count as an open dashboard (/api/alive). */}
      <Route path="overlay" element={<OverlayPage />} />
    </Routes>
  )
}

export default App
