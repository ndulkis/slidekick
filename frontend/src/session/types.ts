import type { SessionState } from '../core/sessionContracts'

export type SessionStatus = 'loading' | 'ready' | 'active' | 'paused' | 'ended' | 'error'

export type PresentationConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export type Gesture = 'next' | 'previous' | 'end' | 'none'

export interface RecognitionEvent {
  gesture: Gesture
  /**
   * Not part of the current RecognitionEvent contract (see
   * sprints/S2-R02-T1-Component-State-Requirements.md). Mocked here until a
   * real confidence source exists.
   */
  confidence?: number
}

export const gestureLabels: Record<Gesture, string> = {
  next: 'Next',
  previous: 'Previous',
  end: 'End',
  none: 'No gesture detected',
}

export const sessionStatusLabels: Record<SessionStatus, string> = {
  loading: 'Session starting',
  ready: 'Ready',
  active: 'Active',
  paused: 'Paused',
  ended: 'Ended',
  error: 'Error',
}

const sessionStateToStatus: Record<SessionState, SessionStatus> = {
  idle: 'ready',
  running: 'active',
  paused: 'paused',
  ended: 'ended',
}

/**
 * Maps the useSession lifecycle state to what the Session components show.
 * Loading and error come from the camera/recognition side, not the session
 * lifecycle, so they're passed in as an override when present.
 */
export function toSessionStatus(
  state: SessionState,
  override?: 'loading' | 'error',
): SessionStatus {
  return override ?? sessionStateToStatus[state]
}

export const presentationStatusLabels: Record<PresentationConnectionStatus, string> = {
  connecting: 'Connecting',
  connected: 'Connected',
  disconnected: 'Disconnected',
  error: 'Error',
}
