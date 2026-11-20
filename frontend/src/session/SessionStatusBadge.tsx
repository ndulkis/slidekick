import pausedIcon from '../assets/robot/paused.svg'
import watchingIcon from '../assets/robot/watching.svg'
import type { SessionStatus } from './types'
import { sessionStatusLabels } from './types'

const statusIcons: Partial<Record<SessionStatus, string>> = {
  active: watchingIcon,
  paused: pausedIcon,
}

interface SessionStatusBadgeProps {
  status: SessionStatus
}

function SessionStatusBadge({ status }: SessionStatusBadgeProps) {
  return (
    <span className={`status-badge status-badge-${status}`} role="status">
      {statusIcons[status] && <img src={statusIcons[status]} alt="" />}
      {sessionStatusLabels[status]}
    </span>
  )
}

export default SessionStatusBadge
