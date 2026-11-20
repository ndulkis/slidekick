import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { api } from '../core/api'
import './Layout.css'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/session', label: 'Session' },
  { to: '/settings', label: 'Settings' },
]

function Layout() {
  const [hasQuit, setHasQuit] = useState(false)

  // An open connection tells SlideKick this window exists. When SlideKick
  // opened the window itself, closing the window quits SlideKick.
  // After Quit it is dropped, so a leftover page doesn't reconnect to the
  // next run and pose as its dashboard.
  useEffect(() => {
    if (hasQuit || typeof EventSource === 'undefined') return
    const alive = new EventSource('/api/alive')
    return () => alive.close()
  }, [hasQuit])

  async function quit() {
    // SlideKick shuts down while replying, so a failed request still means
    // it is quitting (or was already gone).
    await api('/quit', 'POST').catch(() => undefined)
    setHasQuit(true)
  }

  // Rendering this instead of the pages also stops their polling. SlideKick
  // closes its own app window on quit, so this is only seen in a normal
  // browser tab, which a page is not allowed to close.
  if (hasQuit) {
    return (
      <div className="app-shell">
        <main className="app-content" role="status">
          <h1>SlideKick has quit</h1>
          <p>The camera is off. You can close this window.</p>
          <p>
            To use SlideKick again, run <code>slidekick</code>.
          </p>
        </main>
      </div>
    )
  }

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
        <button type="button" className="app-quit" onClick={quit}>
          Quit SlideKick
        </button>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
