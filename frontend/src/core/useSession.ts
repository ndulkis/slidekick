import { useCallback, useEffect, useState } from 'react'
import type { Gesture } from '../session/types'
import { api } from './api'
import type { SessionEvent, SessionEventType, SessionState } from './sessionContracts'

// The Python SessionController owns session state (docs/architecture-decision-note.md).
// This hook polls it and sends the user's actions to it.

export const POLL_INTERVAL_MS = 500

/** connecting until the first reply; offline while SlideKick can't be reached. */
export type Connection = 'connecting' | 'connected' | 'offline'

/** The camera is off until a session starts. error: it failed to open last time. */
export type CameraStatus = 'off' | 'starting' | 'ready' | 'error'

/** The last gesture that ran a presentation command. id changes per gesture. */
export type LastGesture = { id: number; gesture: Gesture; confidence?: number }

type StatusBody = {
  state: SessionState
  camera: CameraStatus
  last_gesture: { id: number; gesture: Gesture; confidence: number | null } | null
  presentation_error: string | null
}

type ActionBody = StatusBody & {
  event?: {
    type: SessionEventType
    previous_state: SessionState
    new_state: SessionState
    use_case: SessionEvent['useCase']
  }
}

type Action = 'start' | 'pause' | 'resume' | 'end'

export function useSession() {
  const [connection, setConnection] = useState<Connection>('connecting')
  const [state, setState] = useState<SessionState>('idle')
  const [camera, setCamera] = useState<CameraStatus>('off')
  const [presentationError, setPresentationError] = useState<string | null>(null)
  const [lastGesture, setLastGesture] = useState<LastGesture | null>(null)

  const apply = useCallback((body: StatusBody) => {
    setConnection('connected')
    setState(body.state)
    setCamera(body.camera)
    setPresentationError(body.presentation_error)
    const next = body.last_gesture
    // Keep the same object while the id is unchanged, so polling doesn't
    // look like a new gesture (the toast re-shows on every new object).
    setLastGesture((prev) =>
      prev?.id === next?.id
        ? prev
        : next && { id: next.id, gesture: next.gesture, confidence: next.confidence ?? undefined },
    )
  }, [])

  useEffect(() => {
    let cancelled = false
    async function poll() {
      try {
        const res = await api<StatusBody>('/session')
        if (!cancelled && res.ok) apply(res.body)
      } catch {
        if (!cancelled) setConnection('offline')
      }
    }
    void poll()
    const timer = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [apply])

  const act = useCallback(
    async (action: Action): Promise<SessionEvent | null> => {
      try {
        const res = await api<ActionBody>(`/session/${action}`, 'POST')
        // A refused transition (409) still carries the current status.
        if (res.body.state) apply(res.body)
        const event = res.ok ? res.body.event : undefined
        if (!event) return null
        return {
          type: event.type,
          previousState: event.previous_state,
          newState: event.new_state,
          useCase: event.use_case,
        }
      } catch {
        setConnection('offline')
        return null
      }
    },
    [apply],
  )

  return {
    connection,
    state,
    camera,
    presentationError,
    lastGesture,
    start: useCallback(() => act('start'), [act]),
    pause: useCallback(() => act('pause'), [act]),
    resume: useCallback(() => act('resume'), [act]),
    end: useCallback(() => act('end'), [act]),
  }
}
