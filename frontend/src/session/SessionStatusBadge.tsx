import type { SessionStatus } from './types'
import { sessionStatusLabels } from './types'

interface SessionStatusBadgeProps {
  status: SessionStatus
}

function SessionStatusBadge({ status }: SessionStatusBadgeProps) {
  return (
    <span className={`status-badge status-badge-${status}`} role="status">
      {sessionStatusLabels[status]}
    </span>
  )
}

export default SessionStatusBadge
