import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import { useSession } from './useSession'

// The transition rules themselves are tested against the real
// SessionController in tests/unit/test_session_controller.py and
// tests/unit/test_api_server.py. These tests cover the hook's use of the API.

async function connectedHook() {
  const hook = renderHook(() => useSession())
  await waitFor(() => expect(hook.result.current.connection).toBe('connected'))
  return hook
}

describe('useSession', () => {
  it('is connecting until the first reply, then shows the backend state', async () => {
    fakeBackend.state = 'paused'
    const { result } = renderHook(() => useSession())
    expect(result.current.connection).toBe('connecting')

    await waitFor(() => expect(result.current.connection).toBe('connected'))
    expect(result.current.state).toBe('paused')
    expect(result.current.camera).toBe('ready')
  })

  it('returns the event and new state for a valid action', async () => {
    const { result } = await connectedHook()

    let event
    await act(async () => {
      event = await result.current.start()
    })

    expect(event).toEqual({
      type: 'session_started',
      previousState: 'idle',
      newState: 'running',
      useCase: 'UC10',
    })
    expect(result.current.state).toBe('running')
    expect(fakeBackend.state).toBe('running')
  })

  it('returns null and keeps the state for a refused action', async () => {
    const { result } = await connectedHook()

    let event
    await act(async () => {
      event = await result.current.pause()
    })

    expect(event).toBeNull()
    expect(result.current.state).toBe('idle')
  })

  it('follows state changed outside the dashboard, e.g. camera window keys', async () => {
    const { result } = await connectedHook()

    fakeBackend.state = 'running'

    await waitFor(() => expect(result.current.state).toBe('running'))
  })

  it('goes offline when SlideKick cannot be reached, and recovers', async () => {
    const { result } = await connectedHook()

    fakeBackend.online = false
    let event
    await act(async () => {
      event = await result.current.start()
    })
    expect(event).toBeNull()
    expect(result.current.connection).toBe('offline')

    fakeBackend.online = true
    await waitFor(() => expect(result.current.connection).toBe('connected'))
  })

  it('reports gestures and keeps the same object until a new one arrives', async () => {
    const { result } = await connectedHook()

    fakeBackend.emitGesture('next', 0.9)
    await waitFor(() => expect(result.current.lastGesture?.gesture).toBe('next'))
    const first = result.current.lastGesture
    expect(first).toEqual({ id: 1, gesture: 'next', confidence: 0.9 })

    // Another poll with the same gesture id keeps the same object.
    await new Promise((resolve) => setTimeout(resolve, 600))
    expect(result.current.lastGesture).toBe(first)

    fakeBackend.emitGesture('previous')
    await waitFor(() => expect(result.current.lastGesture?.gesture).toBe('previous'))
    expect(result.current.lastGesture?.confidence).toBeUndefined()
  })

  it('keeps the action functions stable across renders', async () => {
    const { result, rerender } = await connectedHook()
    const before = result.current

    await act(async () => {
      await result.current.start()
    })
    rerender()

    expect(result.current.start).toBe(before.start)
    expect(result.current.pause).toBe(before.pause)
    expect(result.current.resume).toBe(before.resume)
    expect(result.current.end).toBe(before.end)
  })
})
