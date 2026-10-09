import { useCallback, useRef, useState } from 'react'
import type { SessionEvent, SessionEventType, SessionState } from './sessionContracts'

type Listener = (event: SessionEvent) => void

type Transition = { to: SessionState; useCase: SessionEvent['useCase'] }

// Mirrors the valid-transitions table in docs/session-state-model.md.
// A state/event pair missing here is an invalid transition and is a
// no-op rather than throwing, since UI buttons should already be
// disabled for states that don't support a given action.
const VALID_TRANSITIONS: Record<
  SessionState,
  Partial<Record<SessionEventType, Transition>>
> = {
  idle: {
    session_started: { to: 'running', useCase: 'UC10' },
  },
  running: {
    session_paused: { to: 'paused', useCase: 'UC6' },
    session_ended: { to: 'ended', useCase: 'UC8' },
  },
  paused: {
    session_resumed: { to: 'running', useCase: 'UC7' },
  },
  ended: {
    session_started: { to: 'running', useCase: 'UC10' },
  },
}

export function useSession() {
  const [state, setState] = useState<SessionState>('idle')
  const stateRef = useRef<SessionState>('idle')
  const listeners = useRef<Listener[]>([])

  const subscribe = useCallback((listener: Listener) => {
    listeners.current.push(listener)
    return () => {
      listeners.current = listeners.current.filter((l) => l !== listener)
    }
  }, [])

  const dispatch = useCallback((type: SessionEventType): SessionEvent | null => {
    const previousState = stateRef.current
    const transition = VALID_TRANSITIONS[previousState]?.[type]
    if (!transition) return null

    const event: SessionEvent = {
      type,
      previousState,
      newState: transition.to,
      useCase: transition.useCase,
    }
    stateRef.current = transition.to
    setState(transition.to)
    listeners.current.forEach((listener) => listener(event))
    return event
  }, [])

  return {
    state,
    subscribe,
    start: useCallback(() => dispatch('session_started'), [dispatch]),
    pause: useCallback(() => dispatch('session_paused'), [dispatch]),
    resume: useCallback(() => dispatch('session_resumed'), [dispatch]),
    end: useCallback(() => dispatch('session_ended'), [dispatch]),
  }
}
