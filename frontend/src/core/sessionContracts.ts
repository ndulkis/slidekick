export type SessionState = 'idle' | 'running' | 'paused' | 'ended'

export type SessionEventType =
  | 'session_started'
  | 'session_paused'
  | 'session_resumed'
  | 'session_ended'

export type SessionEvent = {
  type: SessionEventType
  previousState: SessionState
  newState: SessionState
  useCase: 'UC10' | 'UC6' | 'UC7' | 'UC8'
}
