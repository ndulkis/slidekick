import { useEffect } from 'react'
import { useSession } from '../core/useSession'
import GestureFeedbackToast from '../session/GestureFeedbackToast'
import SessionStatusBadge from '../session/SessionStatusBadge'
import { toSessionStatus } from '../session/types'
import './SessionPage.css'
import './OverlayPage.css'

declare global {
  interface Window {
    /** Injected by pywebview in the overlay window (overlay_window.py). */
    pywebview?: { api?: { place?: (position: string) => Promise<void> } }
  }
}

// Shown in a small always-on-top window over the slideshow
// (src/slidekick/overlay_window.py). Empty outside a session, or when turned
// off in Settings. The container always renders, because its presence is what
// makes the page transparent.
function OverlayPage() {
  const session = useSession()
  const inSession = session.state === 'running' || session.state === 'paused'
  const shown = inSession && session.overlay?.enabled !== false
  const status = toSessionStatus(session.state)
  const event = status === 'active' ? (session.lastGesture ?? undefined) : undefined
  const position = session.overlay?.position

  // Move the window to the corner chosen in Settings. pywebview's API may only
  // arrive after the first poll, so also place it once it's ready.
  useEffect(() => {
    if (!position) return
    const place = () => void window.pywebview?.api?.place?.(position)
    place()
    window.addEventListener('pywebviewready', place)
    return () => window.removeEventListener('pywebviewready', place)
  }, [position])

  return (
    <div className={`overlay overlay-${position ?? 'top-right'}`}>
      {shown && (
        <>
          <SessionStatusBadge status={status} />
          <GestureFeedbackToast event={event} />
        </>
      )}
    </div>
  )
}

export default OverlayPage
