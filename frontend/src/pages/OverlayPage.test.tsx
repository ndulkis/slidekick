import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import OverlayPage from './OverlayPage'

describe('OverlayPage', () => {
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
})
