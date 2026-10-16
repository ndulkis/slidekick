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

  return (
    <>
      <button type="button" onClick={onStart} disabled={!canStart}>
        {startLabel}
      </button>
      <button type="button" onClick={onEnd} disabled={!canEnd}>
        End session
      </button>
    </>
  )
}

export default StartEndControl
