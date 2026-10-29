import ConfidenceIndicator from './ConfidenceIndicator'
import type { RecognitionEvent, SessionStatus } from './types'
import { gestureLabels } from './types'

interface GestureFeedbackProps {
  status: SessionStatus
  event?: RecognitionEvent
}

function GestureFeedback({ status, event }: GestureFeedbackProps) {
  if (status === 'loading') {
    return (
      <div className="gesture-feedback" role="status">
        Recognition initializing...
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="gesture-feedback" role="status">
        Recognition unavailable
      </div>
    )
  }

  // Gestures don't control the presentation while paused or after the
  // session ends, so don't show a gesture or confidence that could suggest
  // otherwise.
  if (status === 'paused') {
    return (
      <div className="gesture-feedback" role="status">
        Gesture recognition paused
      </div>
    )
  }

  if (status === 'ended') {
    return (
      <div className="gesture-feedback" role="status">
        Gesture recognition off
      </div>
    )
  }

  const gesture = event?.gesture ?? 'none'

  return (
    <div className="gesture-feedback" role="status">
      <span>{gestureLabels[gesture]}</span>
      {gesture !== 'none' && <ConfidenceIndicator confidence={event?.confidence} />}
    </div>
  )
}

export default GestureFeedback
