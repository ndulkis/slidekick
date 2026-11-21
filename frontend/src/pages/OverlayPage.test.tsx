import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import OverlayPage from './OverlayPage'

async function startSession() {
  fakeBackend.state = 'running'
  fakeBackend.camera = 'ready'
  render(<OverlayPage />)
  expect(await screen.findByText('Active')).toBeInTheDocument()
}

describe('OverlayPage', () => {
  afterEach(() => {
    delete window.pywebview
  })

  it('shows status and gesture feedback only during a session', async () => {
    const { rerender } = render(<OverlayPage />)
    // Outside a session: an empty container, which keeps the page transparent.
    await waitFor(() => expect(document.querySelector('.overlay')).toBeEmptyDOMElement())

    fakeBackend.state = 'running'
    fakeBackend.camera = 'ready'
    expect(await screen.findByText('Active')).toBeInTheDocument()

    fakeBackend.emitGesture('next', 0.9)
    expect(await screen.findByText('Next')).toBeInTheDocument()

    fakeBackend.state = 'paused'
    rerender(<OverlayPage />)
    expect(await screen.findByText('Paused')).toBeInTheDocument()
    // Gestures don't control the slides while paused.
    expect(screen.queryByText('Next')).toBeNull()
  })

  it('shows nothing once turned off in Settings, even mid-session', async () => {
    await startSession()

    fakeBackend.overlay = { enabled: false, position: 'top-right' }

    await waitFor(() => expect(screen.queryByText('Active')).toBeNull())
    expect(document.querySelector('.overlay')).toBeEmptyDOMElement()
  })

  it('moves its window to the corner chosen in Settings', async () => {
    const place = vi.fn(() => Promise.resolve())
    window.pywebview = { api: { place } }
    await startSession()
    expect(place).toHaveBeenLastCalledWith('top-right')

    fakeBackend.overlay = { enabled: true, position: 'bottom-left' }

    await waitFor(() => expect(place).toHaveBeenLastCalledWith('bottom-left'))
    expect(document.querySelector('.overlay')).toHaveClass('overlay-bottom-left')
  })
})
