import type { PresentationConnectionStatus } from './types'
import { presentationStatusLabels } from './types'

interface PresentationStatusProps {
  status: PresentationConnectionStatus
}

function PresentationStatus({ status }: PresentationStatusProps) {
  return (
    <span
      className={`presentation-status presentation-status-${status}`}
      role="status"
    >
      Presentation: {presentationStatusLabels[status]}
    </span>
  )
}

export default PresentationStatus
