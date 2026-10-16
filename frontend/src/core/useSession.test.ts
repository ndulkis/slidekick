import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { SessionEvent, SessionState } from './sessionContracts'
import { useSession } from './useSession'

// The transition tables in docs/session-state-model.md are the source of
// truth. These tests mirror the Python tests in tests/unit/test_session_controller.py.

type Operation = 'start' | 'pause' | 'resume' | 'end'

// Public operations that reach each state, starting from a new hook.
const PATH_TO_STATE: Record<SessionState, Operation[]> = {
  idle: [],
  running: ['start'],
  paused: ['start', 'pause'],
  ended: ['start', 'end'],
}

function hookIn(state: SessionState) {
  const hook = renderHook(() => useSession())
  for (const operation of PATH_TO_STATE[state]) {
    act(() => {
      hook.result.current[operation]()
    })
  }
  return hook
}

describe('useSession', () => {
  it('starts idle', () => {
    const { result } = renderHook(() => useSession())

    expect(result.current.state).toBe('idle')
  })

  describe('valid transitions', () => {
    const validTransitions: Array<{
      from: SessionState
      operation: Operation
      expected: SessionEvent
    }> = [
      {
        from: 'idle',
        operation: 'start',
        expected: {
          type: 'session_started',
          previousState: 'idle',
          newState: 'running',
          useCase: 'UC10',
        },
      },
      {
        from: 'running',
        operation: 'pause',
        expected: {
          type: 'session_paused',
          previousState: 'running',
          newState: 'paused',
          useCase: 'UC6',
        },
      },
      {
        from: 'paused',
        operation: 'resume',
        expected: {
          type: 'session_resumed',
          previousState: 'paused',
          newState: 'running',
          useCase: 'UC7',
        },
      },
      {
        from: 'running',
        operation: 'end',
        expected: {
          type: 'session_ended',
          previousState: 'running',
          newState: 'ended',
          useCase: 'UC8',
        },
      },
      {
        // Restart is drawn in the state diagram as UC10 from ended back to running.
        from: 'ended',
        operation: 'start',
        expected: {
          type: 'session_started',
          previousState: 'ended',
          newState: 'running',
          useCase: 'UC10',
        },
      },
    ]

    it.each(validTransitions)(
      '$operation from $from moves to $expected.newState and emits one event',
      ({ from, operation, expected }) => {
        const { result } = hookIn(from)
        const listener = vi.fn()
        result.current.subscribe(listener)

        let returned: SessionEvent | null = null
        act(() => {
          returned = result.current[operation]()
        })

        expect(result.current.state).toBe(expected.newState)
        expect(returned).toEqual(expected)
        expect(listener).toHaveBeenCalledTimes(1)
        expect(listener).toHaveBeenCalledWith(expected)
      },
    )
  })

  describe('invalid transitions', () => {
    const invalidTransitions: Array<{ from: SessionState; operation: Operation }> = [
      { from: 'idle', operation: 'pause' },
      { from: 'idle', operation: 'resume' },
      { from: 'idle', operation: 'end' },
      { from: 'running', operation: 'start' },
      { from: 'running', operation: 'resume' },
      { from: 'paused', operation: 'start' },
      { from: 'paused', operation: 'pause' },
      // The state diagram has no edge from paused to ended, so a paused
      // session must be resumed first. This is the open question in
      // docs/session-state-model.md. If the team allows ending from
      // paused, change this case together with the hook.
      { from: 'paused', operation: 'end' },
      { from: 'ended', operation: 'pause' },
      { from: 'ended', operation: 'resume' },
      { from: 'ended', operation: 'end' },
    ]

    it.each(invalidTransitions)(
      '$operation from $from is ignored: no state change, no event',
      ({ from, operation }) => {
        const { result } = hookIn(from)
        const listener = vi.fn()
        result.current.subscribe(listener)

        let returned: SessionEvent | null = null
        act(() => {
          returned = result.current[operation]()
        })

        expect(returned).toBeNull()
        expect(result.current.state).toBe(from)
        expect(listener).not.toHaveBeenCalled()
      },
    )
  })

  describe('subscriptions', () => {
    it('notifies every subscriber with the same event', () => {
      const { result } = renderHook(() => useSession())
      const first = vi.fn()
      const second = vi.fn()
      result.current.subscribe(first)
      result.current.subscribe(second)

      act(() => {
        result.current.start()
      })

      expect(first).toHaveBeenCalledTimes(1)
      expect(second).toHaveBeenCalledTimes(1)
      expect(first.mock.calls[0][0]).toBe(second.mock.calls[0][0])
    })

    it('stops notifying a subscriber after it unsubscribes', () => {
      const { result } = renderHook(() => useSession())
      const listener = vi.fn()
      const unsubscribe = result.current.subscribe(listener)

      act(() => {
        result.current.start()
      })
      unsubscribe()
      act(() => {
        result.current.pause()
      })

      expect(listener).toHaveBeenCalledTimes(1)
      expect(listener.mock.calls[0][0].type).toBe('session_started')
    })

    it('keeps other subscribers when one unsubscribes', () => {
      const { result } = renderHook(() => useSession())
      const removed = vi.fn()
      const kept = vi.fn()
      const unsubscribe = result.current.subscribe(removed)
      result.current.subscribe(kept)

      unsubscribe()
      act(() => {
        result.current.start()
      })

      expect(removed).not.toHaveBeenCalled()
      expect(kept).toHaveBeenCalledTimes(1)
    })
  })

  describe('full lifecycle', () => {
    it('emits events in order and chains each previousState to the last newState', () => {
      const { result } = renderHook(() => useSession())
      const events: SessionEvent[] = []
      result.current.subscribe((event) => events.push(event))

      act(() => {
        result.current.start()
      })
      act(() => {
        result.current.pause()
      })
      act(() => {
        result.current.resume()
      })
      act(() => {
        result.current.end()
      })
      act(() => {
        result.current.start()
      })

      expect(events.map((event) => event.type)).toEqual([
        'session_started',
        'session_paused',
        'session_resumed',
        'session_ended',
        'session_started',
      ])
      expect(events[0].previousState).toBe('idle')
      events.slice(1).forEach((event, index) => {
        expect(event.previousState).toBe(events[index].newState)
      })
      events.forEach((event) => {
        expect(event.previousState).not.toBe(event.newState)
      })
      expect(result.current.state).toBe('running')
    })
  })

  it('keeps the action functions stable across renders', () => {
    const { result, rerender } = renderHook(() => useSession())
    const before = result.current

    act(() => {
      result.current.start()
    })
    rerender()

    expect(result.current.start).toBe(before.start)
    expect(result.current.pause).toBe(before.pause)
    expect(result.current.resume).toBe(before.resume)
    expect(result.current.end).toBe(before.end)
    expect(result.current.subscribe).toBe(before.subscribe)
  })
})
