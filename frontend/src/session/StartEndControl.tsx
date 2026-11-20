import type { SessionStatus } from './types'

interface StartEndControlProps {
  status: SessionStatus
  onStart: () => void
  onEnd: () => void
}

function StartEndControl({ status, onStart, onEnd }: StartEndControlProps) {
  // Matches the valid transitions in docs/session-state-model.md: start from
  // idle or ended, end only from running (not while paused).
  const canStart = status === 'ready' || status === 'ended'
  const canEnd = status === 'active'
  const startLabel = status === 'ended' ? 'Start new session' : 'Start session'
  // One big action at a time: Start outside a session, End during one. The
  // other stays in the page (disabled) so the order and states don't change.
  const inSession = status === 'active' || status === 'paused'

  return (
    <>
      <button
        type="button"
        className={inSession ? 'button-primary button-collapsed' : 'button-primary'}
        onClick={onStart}
        disabled={!canStart}
      >
        {startLabel}
      </button>
      <button
        type="button"
        className={inSession ? 'button-danger' : 'button-danger button-collapsed'}
        onClick={onEnd}
        disabled={!canEnd}
      >
        End session
      </button>
    </>
  )
}

export default StartEndControl
