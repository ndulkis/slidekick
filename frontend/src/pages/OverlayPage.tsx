import { useSession } from '../core/useSession'
import GestureFeedbackToast from '../session/GestureFeedbackToast'
import SessionStatusBadge from '../session/SessionStatusBadge'
import { toSessionStatus } from '../session/types'
import './SessionPage.css'
import './OverlayPage.css'

// Shown in a small always-on-top window over the slideshow
// (src/slidekick/overlay_window.py). Empty outside a session. The container
// always renders, because its presence is what makes the page transparent.
function OverlayPage() {
  const session = useSession()
  const inSession = session.state === 'running' || session.state === 'paused'
  const status = toSessionStatus(session.state)
  const event = status === 'active' ? (session.lastGesture ?? undefined) : undefined

  return (
    <div className="overlay">
      {inSession && (
        <>
          <SessionStatusBadge status={status} />
          <GestureFeedbackToast event={event} />
        </>
      )}
    </div>
  )
}

export default OverlayPage
