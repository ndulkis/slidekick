import { useState } from 'react'
import { useSession } from '../core/useSession'
import CameraPreview from '../session/CameraPreview'
import GestureFeedback from '../session/GestureFeedback'
import GestureFeedbackToast from '../session/GestureFeedbackToast'
import PauseResumeControl from '../session/PauseResumeControl'
import PresentationStatus from '../session/PresentationStatus'
import SessionMessage from '../session/SessionMessage'
import SessionStatusBadge from '../session/SessionStatusBadge'
import StartEndControl from '../session/StartEndControl'
import type { PresentationConnectionStatus, RecognitionEvent } from '../session/types'
import { toSessionStatus } from '../session/types'
import './SessionPage.css'

const demoGestures: RecognitionEvent[] = [
  { gesture: 'next', confidence: 0.92 },
  { gesture: 'previous', confidence: 0.81 },
  { gesture: 'end', confidence: 0.75 },
  { gesture: 'none' },
]

function SessionPage() {
  const session = useSession()
  // Loading and error come from the camera/recognition side, which isn't
  // connected yet, so they're simulated with the demo controls below.
  const [override, setOverride] = useState<'loading' | 'error' | undefined>(undefined)
  const [presentationStatus, setPresentationStatus] =
    useState<PresentationConnectionStatus>('connected')
  const [hasCamera, setHasCamera] = useState(true)
  const [event, setEvent] = useState<RecognitionEvent | undefined>(undefined)

  const status = toSessionStatus(session.state, override)
  // Gestures only control the presentation while the session is active.
  const visibleEvent = status === 'active' ? event : undefined

  // Clear the last gesture on every session change so an old gesture doesn't
  // reappear as if it were new (e.g. after Pause -> Resume).
  function withClearedGesture(action: () => void) {
    return () => {
      setEvent(undefined)
      action()
    }
  }

  return (
    <section>
      <h1>Presentation Session</h1>

      <div className="session-status-row">
        <SessionStatusBadge status={status} />
        <PresentationStatus status={presentationStatus} />
      </div>

      <SessionMessage status={status} />

      <CameraPreview status={status} hasCamera={hasCamera} />

      <GestureFeedback status={status} event={visibleEvent} />

      <GestureFeedbackToast event={visibleEvent} />

      <div className="session-controls">
        <StartEndControl
          status={status}
          onStart={withClearedGesture(session.start)}
          onEnd={withClearedGesture(session.end)}
        />
        <PauseResumeControl
          status={status}
          onPause={withClearedGesture(session.pause)}
          onResume={withClearedGesture(session.resume)}
        />
      </div>

      <div className="session-demo-controls">
        <h2>Demo controls</h2>
        <p>
          SlideKick isn't connected to a real camera or gesture recognition
          backend yet. These buttons simulate outside inputs for testing and
          the usability walkthrough.
        </p>

        <fieldset>
          <legend>Camera and recognition</legend>
          <button type="button" onClick={() => setOverride('loading')}>
            simulate loading
          </button>
          <button type="button" onClick={() => setOverride('error')}>
            simulate error
          </button>
          <button type="button" onClick={() => setOverride(undefined)}>
            clear
          </button>
        </fieldset>

        <fieldset>
          <legend>Presentation connection</legend>
          {(
            ['connecting', 'connected', 'disconnected', 'error'] as PresentationConnectionStatus[]
          ).map((s) => (
            <button key={s} type="button" onClick={() => setPresentationStatus(s)}>
              {s}
            </button>
          ))}
        </fieldset>

        <fieldset>
          <legend>Camera</legend>
          <button type="button" onClick={() => setHasCamera(true)}>
            camera available
          </button>
          <button type="button" onClick={() => setHasCamera(false)}>
            camera unavailable
          </button>
        </fieldset>

        <fieldset>
          <legend>Gesture</legend>
          {demoGestures.map((g) => (
            <button key={g.gesture} type="button" onClick={() => setEvent(g)}>
              {g.gesture}
            </button>
          ))}
        </fieldset>
      </div>
    </section>
  )
}

export default SessionPage
