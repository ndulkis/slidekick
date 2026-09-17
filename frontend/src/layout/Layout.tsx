import { NavLink, Outlet } from 'react-router-dom'
import './Layout.css'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/session', label: 'Session' },
  { to: '/settings', label: 'Settings' },
]

function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">SlideKick</span>
        <nav className="app-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? 'app-nav-link active' : 'app-nav-link'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
