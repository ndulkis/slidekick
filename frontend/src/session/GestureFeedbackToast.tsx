import { useEffect, useState } from 'react'
import type { RecognitionEvent } from './types'
import { gestureLabels } from './types'

interface GestureFeedbackToastProps {
  event?: RecognitionEvent
}

function GestureFeedbackToast({ event }: GestureFeedbackToastProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!event || event.gesture === 'none') {
      return
    }
    // Synchronizing with a timer (an external system), not deriving render
    // state — the toast must reset its auto-hide countdown on every new event.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setVisible(true)
    const timer = setTimeout(() => setVisible(false), 2000)
    return () => clearTimeout(timer)
  }, [event])

  if (!event || event.gesture === 'none' || !visible) {
    return null
  }

  return (
    <div className="gesture-toast" role="status">
      {gestureLabels[event.gesture]}
    </div>
  )
}

export default GestureFeedbackToast
