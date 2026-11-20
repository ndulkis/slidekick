import type { SessionStatus } from './types'

interface PauseResumeControlProps {
  status: SessionStatus
  onPause: () => void
  onResume: () => void
}

function PauseResumeControl({ status, onPause, onResume }: PauseResumeControlProps) {
  const disabled =
    status === 'loading' || status === 'error' || status === 'ready' || status === 'ended'

  // Only shown during a session; elsewhere it stays in the page, disabled.
  const className = disabled ? 'button-collapsed' : undefined

  if (status === 'paused') {
    return (
      <button
        type="button"
        className={className}
        onClick={onResume}
        disabled={disabled}
        aria-label="Resume session"
      >
        Resume
      </button>
    )
  }

  return (
    <button
      type="button"
      className={className}
      onClick={onPause}
      disabled={disabled}
      aria-label="Pause session"
    >
      Pause
    </button>
  )
}

export default PauseResumeControl
