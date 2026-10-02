import { useState } from 'react'
import CameraPreview from '../session/CameraPreview'
import GestureFeedback from '../session/GestureFeedback'
import GestureFeedbackToast from '../session/GestureFeedbackToast'
import PauseResumeControl from '../session/PauseResumeControl'
import PresentationStatus from '../session/PresentationStatus'
import SessionMessage from '../session/SessionMessage'
import SessionStatusBadge from '../session/SessionStatusBadge'
import type { PresentationConnectionStatus, RecognitionEvent, SessionStatus } from '../session/types'
import './SessionPage.css'

const demoGestures: RecognitionEvent[] = [
  { gesture: 'next', confidence: 0.92 },
  { gesture: 'previous', confidence: 0.81 },
  { gesture: 'end', confidence: 0.75 },
  { gesture: 'none' },
]

function SessionPage() {
  const [status, setStatus] = useState<SessionStatus>('ready')
  const [presentationStatus, setPresentationStatus] =
    useState<PresentationConnectionStatus>('connected')
  const [hasCamera, setHasCamera] = useState(true)
  const [event, setEvent] = useState<RecognitionEvent | undefined>(undefined)

  function handlePause() {
    setStatus('paused')
  }

  function handleResume() {
    setStatus('active')
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

      <GestureFeedback status={status} event={event} />

      <GestureFeedbackToast event={event} />

      <PauseResumeControl status={status} onPause={handlePause} onResume={handleResume} />

      <div className="session-demo-controls">
        <h2>Demo controls</h2>
        <p>
          SlideKick isn't connected to a real camera or gesture recognition
          backend yet. These buttons simulate state changes for testing and
          the usability walkthrough.
        </p>

        <fieldset>
          <legend>Session status</legend>
          {(['loading', 'ready', 'active', 'paused', 'error'] as SessionStatus[]).map((s) => (
            <button key={s} type="button" onClick={() => setStatus(s)}>
              {s}
            </button>
          ))}
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
