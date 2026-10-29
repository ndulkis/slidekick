import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SessionMessage from './SessionMessage'

describe('SessionMessage', () => {
  it('shows the starting message when loading', () => {
    render(<SessionMessage status="loading" />)
    expect(screen.getByRole('status')).toHaveTextContent(
      'Starting camera and gesture recognition...',
    )
  })

  it('shows the ready message when ready', () => {
    render(<SessionMessage status="ready" />)
    expect(screen.getByRole('status')).toHaveTextContent(
      'SlideKick is ready. Start a session to begin.',
    )
  })

  it('shows that gestures control the presentation when active', () => {
    render(<SessionMessage status="active" />)
    expect(screen.getByRole('status')).toHaveTextContent(
      'Gesture recognition is on. Gestures will control your presentation.',
    )
  })

  it('shows that gestures are paused when paused', () => {
    render(<SessionMessage status="paused" />)
    expect(screen.getByRole('status')).toHaveTextContent(
      'Gesture recognition paused. Gestures will not control your presentation.',
    )
  })

  it('shows the ended message when ended', () => {
    render(<SessionMessage status="ended" />)
    expect(screen.getByRole('status')).toHaveTextContent(
      "Session ended. Start a new session when you're ready.",
    )
  })

  it('uses an alert for the error message', () => {
    render(<SessionMessage status="error" />)
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Something required by this session is unavailable. Check camera access and try again.',
    )
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
