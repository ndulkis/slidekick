import type { SessionStatus } from './types'

interface PauseResumeControlProps {
  status: SessionStatus
  onPause: () => void
  onResume: () => void
}

function PauseResumeControl({ status, onPause, onResume }: PauseResumeControlProps) {
  const disabled = status === 'loading' || status === 'error' || status === 'ready'

  if (status === 'paused') {
    return (
      <button type="button" onClick={onResume} disabled={disabled} aria-label="Resume session">
        Resume
      </button>
    )
  }

  return (
    <button type="button" onClick={onPause} disabled={disabled} aria-label="Pause session">
      Pause
    </button>
  )
}

export default PauseResumeControl
