import { useSession } from '../core/useSession'
import CameraPreview from '../session/CameraPreview'
import GestureFeedback from '../session/GestureFeedback'
import GestureFeedbackToast from '../session/GestureFeedbackToast'
import PauseResumeControl from '../session/PauseResumeControl'
import PresentationStatus from '../session/PresentationStatus'
import SessionMessage from '../session/SessionMessage'
import SessionStatusBadge from '../session/SessionStatusBadge'
import StartEndControl from '../session/StartEndControl'
import type { PresentationConnectionStatus } from '../session/types'
import { toSessionStatus } from '../session/types'
import './SessionPage.css'

function SessionPage() {
  const session = useSession()
  const { connection, camera } = session

  // Loading and error come from the connection and the camera, not the
  // session lifecycle.
  const override =
    connection === 'offline' || camera === 'error'
      ? 'error'
      : connection === 'connecting' || camera === 'starting'
        ? 'loading'
        : undefined
  const status = toSessionStatus(session.state, override)

  const presentationStatus: PresentationConnectionStatus =
    connection === 'offline'
      ? 'disconnected'
      : connection === 'connecting'
        ? 'connecting'
        : session.presentationError
          ? 'error'
          : 'connected'

  // Gestures only control the presentation while the session is active. The
  // backend clears the last gesture on every session change.
  const visibleEvent = status === 'active' ? (session.lastGesture ?? undefined) : undefined

  return (
    <section>
      <h1>Presentation Session</h1>

      <div className="session-status-row">
        <SessionStatusBadge status={status} />
        <PresentationStatus status={presentationStatus} />
      </div>

      <SessionMessage status={status} />

      {connection === 'offline' && (
        <p className="session-message">
          Can't reach SlideKick. Start it with{' '}
          <code>PYTHONPATH=src python scripts/run_gesture_control.py</code>.
        </p>
      )}
      {session.presentationError && (
        <p className="session-message">{session.presentationError}</p>
      )}

      <CameraPreview status={status} hasCamera={camera !== 'error'} />

      <GestureFeedback status={status} event={visibleEvent} />

      <GestureFeedbackToast event={visibleEvent} />

      <div className="session-controls">
        <StartEndControl status={status} onStart={session.start} onEnd={session.end} />
        <PauseResumeControl
          status={status}
          onPause={session.pause}
          onResume={session.resume}
        />
      </div>
    </section>
  )
}

export default SessionPage
