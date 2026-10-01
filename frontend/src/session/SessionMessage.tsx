import type { SessionStatus } from './types'

interface SessionMessageProps {
  status: SessionStatus
}

const messages: Partial<Record<SessionStatus, string>> = {
  loading: 'Starting camera and gesture recognition...',
  ready: 'SlideKick is ready. Start a session to begin.',
  error:
    'Something required by this session is unavailable. Check camera access and try again.',
}

function SessionMessage({ status }: SessionMessageProps) {
  const message = messages[status]

  if (!message) {
    return null
  }

  return (
    <p className="session-message" role={status === 'error' ? 'alert' : 'status'}>
      {message}
    </p>
  )
}

export default SessionMessage
