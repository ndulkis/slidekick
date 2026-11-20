import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import errorIcon from '../assets/robot/error.svg'
import loadingIcon from '../assets/robot/loading.svg'
import successIcon from '../assets/robot/success.svg'
import { api } from '../core/api'
import { useSession } from '../core/useSession'
import './DashboardPage.css'

type Check = 'ok' | 'problem' | 'waiting'

interface ChecklistItem {
  label: string
  check: Check
  detail: string
}

type CamerasBody = { cameras: { id: string; name: string }[]; selected: string | null }

const checkLabels: Record<Check, string> = {
  ok: 'OK',
  problem: 'Needs attention',
  waiting: 'Checking',
}

const sessionLabels = {
  idle: 'Not started',
  running: 'Running',
  paused: 'Paused',
  ended: 'Ended',
} as const

/** A "ready to present?" checklist built from what SlideKick reports. */
function DashboardPage() {
  const session = useSession()
  const { connection } = session
  const [cameras, setCameras] = useState<CamerasBody | null>(null)

  // Asked again once SlideKick is reachable, since the first try may have
  // been before it started.
  useEffect(() => {
    if (connection !== 'connected') return
    let cancelled = false
    api<CamerasBody>('/cameras').then(
      (res) => {
        if (!cancelled && res.ok) setCameras(res.body)
      },
      () => {},
    )
    return () => {
      cancelled = true
    }
  }, [connection])

  const selectedCamera = cameras?.cameras.find((c) => c.id === cameras.selected)

  const items: ChecklistItem[] = [
    connection === 'offline'
      ? { label: 'SlideKick', check: 'problem', detail: "Can't reach SlideKick. Start it with slidekick." }
      : connection === 'connecting'
        ? { label: 'SlideKick', check: 'waiting', detail: 'Connecting...' }
        : { label: 'SlideKick', check: 'ok', detail: 'Running' },
    connection !== 'connected' || cameras === null
      ? { label: 'Camera', check: 'waiting', detail: 'Looking for cameras...' }
      : session.camera === 'error'
        ? { label: 'Camera', check: 'problem', detail: "The camera couldn't start. Check camera access." }
        : selectedCamera
          ? { label: 'Camera', check: 'ok', detail: selectedCamera.name }
          : { label: 'Camera', check: 'problem', detail: 'No camera found. Connect one.' },
    session.presentationError
      ? { label: 'Slide control', check: 'problem', detail: session.presentationError }
      : connection === 'connected'
        ? { label: 'Slide control', check: 'ok', detail: 'Ready to send slide changes' }
        : { label: 'Slide control', check: 'waiting', detail: 'Waiting for SlideKick...' },
  ]

  const overall: Check = items.some((i) => i.check === 'problem')
    ? 'problem'
    : items.some((i) => i.check === 'waiting')
      ? 'waiting'
      : 'ok'
  const icon = { ok: successIcon, problem: errorIcon, waiting: loadingIcon }[overall]
  const summary = {
    ok: 'Ready to present',
    problem: 'Something needs attention',
    waiting: 'Checking your setup...',
  }[overall]
  const inSession = session.state === 'running' || session.state === 'paused'

  return (
    <section>
      <h1>Dashboard</h1>

      <div className="dashboard-card">
        <div className="dashboard-summary">
          <img src={icon} alt="" />
          <p className="dashboard-summary-text" role="status">
            {summary}
          </p>
        </div>

        <ul className="dashboard-checklist">
          {items.map((item) => (
            <li key={item.label} className={`dashboard-check dashboard-check-${item.check}`}>
              <span className="dashboard-check-mark" aria-hidden="true" />
              <span className="dashboard-check-label">{item.label}</span>
              <span className="dashboard-check-detail">
                <span className="visually-hidden">{checkLabels[item.check]}: </span>
                {item.detail}
              </span>
            </li>
          ))}
          <li className="dashboard-check dashboard-check-info">
            <span className="dashboard-check-mark" aria-hidden="true" />
            <span className="dashboard-check-label">Session</span>
            <span className="dashboard-check-detail">{sessionLabels[session.state]}</span>
          </li>
        </ul>

        <Link to="/session" className="button-link button-primary">
          {inSession ? 'Back to the session' : 'Go to Session'}
        </Link>
      </div>
    </section>
  )
}

export default DashboardPage
