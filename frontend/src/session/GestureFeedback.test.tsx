import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import GestureFeedback from './GestureFeedback'

describe('GestureFeedback', () => {
  it('shows an initializing message while loading', () => {
    render(<GestureFeedback status="loading" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Recognition initializing...')
    expect(screen.queryByText(/confidence/i)).not.toBeInTheDocument()
  })

  it('shows an unavailable message on error', () => {
    render(<GestureFeedback status="error" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Recognition unavailable')
    expect(screen.queryByText(/confidence/i)).not.toBeInTheDocument()
  })

  it('defaults to "no gesture detected" when there is no event', () => {
    render(<GestureFeedback status="ready" />)
    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
    expect(screen.queryByText('Confidence unavailable')).not.toBeInTheDocument()
    expect(screen.queryByText(/% confidence/)).not.toBeInTheDocument()
  })

  it('shows the gesture and confidence when both are present', () => {
    render(<GestureFeedback status="active" event={{ gesture: 'next', confidence: 0.92 }} />)
    expect(screen.getByText('Next')).toBeInTheDocument()
    expect(screen.getByText('92% confidence')).toBeInTheDocument()
    expect(screen.getByLabelText('Confidence 92%')).toBeInTheDocument()
  })

  it('shows the gesture with unavailable confidence when confidence is missing', () => {
    render(<GestureFeedback status="active" event={{ gesture: 'next' }} />)
    expect(screen.getByText('Next')).toBeInTheDocument()
    expect(screen.getByText('Confidence unavailable')).toBeInTheDocument()
  })

  it('skips the confidence indicator entirely when gesture is none', () => {
    render(
      <GestureFeedback status="paused" event={{ gesture: 'none', confidence: 0.92 }} />,
    )

    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
    expect(screen.queryByText('92% confidence')).not.toBeInTheDocument()
    expect(screen.queryByText('Confidence unavailable')).not.toBeInTheDocument()
  })
})
