import { useSession } from '../core/useSession'
import CameraPicker from '../settings/CameraPicker'
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
  // session lifecycle. A camera that failed to open ends the session, so the
  // user can try Start again.
  const override =
    connection === 'offline'
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
          Can't reach SlideKick. Start it with <code>slidekick</code>.
        </p>
      )}
      {session.presentationError && (
        <p className="session-message">{session.presentationError}</p>
      )}

      {camera === 'error' && (
        <p className="session-message" role="alert">
          The camera couldn't start.{' '}
          {navigator.userAgent.includes('Windows')
            ? 'Turn on "Let desktop apps access your camera" in Settings > Privacy & security > Camera'
            : 'Check camera access for the terminal running SlideKick'}
          , then start a new session.
        </p>
      )}

      <div className="session-main">
        {/* The gesture toast shows over the preview, where the presenter is
            already looking to check the camera sees them. */}
        <div className="session-stage">
          <CameraPreview
            status={status}
            hasCamera={camera !== 'error'}
            switching={session.cameraSwitching}
          />
          <GestureFeedbackToast event={visibleEvent} />
        </div>

        <div className="session-panel">
          {/* Shows the camera in use, so a failed switch shows the camera kept. */}
          <CameraPicker disabled={camera === 'starting'} selected={session.cameraId} />
          {session.cameraMessage && (
            <p className="session-message" role="alert">
              {session.cameraMessage}
            </p>
          )}

          <div className="session-controls">
            <StartEndControl status={status} onStart={session.start} onEnd={session.end} />
            <PauseResumeControl
              status={status}
              onPause={session.pause}
              onResume={session.resume}
            />
          </div>

          <GestureFeedback status={status} event={visibleEvent} />
        </div>
      </div>
    </section>
  )
}

export default SessionPage
