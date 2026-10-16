import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SessionPage from './SessionPage'

function button(name: string) {
  return screen.getByRole('button', { name })
}

function badge() {
  return screen.getByText(/^(Session starting|Ready|Active|Paused|Ended|Error)$/)
}

function startSession() {
  fireEvent.click(button('Start session'))
}

describe('SessionPage', () => {
  it('renders the default Ready state', () => {
    render(<SessionPage />)
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('Presentation: Connected')).toBeInTheDocument()
    expect(button('Start session')).toBeEnabled()
  })

  it('shows camera unavailable message when camera is missing', () => {
    render(<SessionPage />)
    fireEvent.click(button('camera unavailable'))
    expect(screen.getByText('No camera source is available.')).toBeInTheDocument()
  })

  it('switches to Active and shows Pause control after Start', () => {
    render(<SessionPage />)
    startSession()
    expect(badge()).toHaveTextContent('Active')
    expect(button('Pause session')).toBeEnabled()
  })

  it('shows gesture feedback with confidence when a gesture is selected', () => {
    render(<SessionPage />)
    startSession()
    fireEvent.click(button('next'))
    expect(screen.getAllByText('Next').length).toBeGreaterThan(0)
    expect(screen.getByText('92% confidence')).toBeInTheDocument()
  })

  it('treats no-gesture as a normal state, not an error', () => {
    render(<SessionPage />)
    startSession()
    fireEvent.click(button('none'))
    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
  })

  it('shows the error message when an error is simulated', () => {
    render(<SessionPage />)
    fireEvent.click(button('simulate error'))
    expect(
      screen.getByText(
        'Something required by this session is unavailable. Check camera access and try again.',
      ),
    ).toBeInTheDocument()
  })

  it('walks through start, pause, resume, and end', () => {
    render(<SessionPage />)

    startSession()
    expect(badge()).toHaveTextContent('Active')
    expect(button('End session')).toBeEnabled()

    fireEvent.click(button('Pause session'))
    expect(badge()).toHaveTextContent('Paused')
    // The session state model doesn't allow ending while paused.
    expect(button('End session')).toBeDisabled()

    fireEvent.click(button('Resume session'))
    expect(badge()).toHaveTextContent('Active')
    expect(button('End session')).toBeEnabled()

    fireEvent.click(button('End session'))
    expect(badge()).toHaveTextContent('Ended')
    expect(button('Start new session')).toBeEnabled()
    expect(button('Pause session')).toBeDisabled()
  })

  it('shows a message for each session state', () => {
    render(<SessionPage />)

    startSession()
    expect(
      screen.getByText('Gesture recognition is on. Gestures will control your presentation.'),
    ).toBeInTheDocument()

    fireEvent.click(button('Pause session'))
    expect(
      screen.getByText('Gesture recognition paused. Gestures will not control your presentation.'),
    ).toBeInTheDocument()

    fireEvent.click(button('Resume session'))
    fireEvent.click(button('End session'))
    expect(
      screen.getByText("Session ended. Start a new session when you're ready."),
    ).toBeInTheDocument()
    expect(screen.getByText('Camera off')).toBeInTheDocument()
  })

  it('does not show gestures while paused', () => {
    render(<SessionPage />)
    startSession()
    fireEvent.click(button('Pause session'))

    fireEvent.click(button('next'))

    expect(screen.getByText('Gesture recognition paused')).toBeInTheDocument()
    expect(screen.queryByText('Next')).not.toBeInTheDocument()
    expect(screen.queryByText('92% confidence')).not.toBeInTheDocument()
  })

  it('clears the last gesture after pausing and resuming', () => {
    render(<SessionPage />)
    startSession()
    fireEvent.click(button('next'))
    expect(screen.getByText('92% confidence')).toBeInTheDocument()

    fireEvent.click(button('Pause session'))
    fireEvent.click(button('Resume session'))

    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
    expect(screen.queryByText('92% confidence')).not.toBeInTheDocument()
  })

  it('blocks actions that are not valid in the current state', () => {
    render(<SessionPage />)

    startSession()
    expect(button('Start session')).toBeDisabled()

    fireEvent.click(button('Pause session'))
    expect(screen.queryByRole('button', { name: 'Pause session' })).not.toBeInTheDocument()
    expect(button('Resume session')).toBeEnabled()
    expect(button('Start session')).toBeDisabled()
  })

  it('can start a new session after ending', () => {
    render(<SessionPage />)
    startSession()
    fireEvent.click(button('End session'))

    fireEvent.click(button('Start new session'))
    expect(badge()).toHaveTextContent('Active')
    expect(button('End session')).toBeEnabled()
  })

  it('disables session controls during an error and recovers when cleared', () => {
    render(<SessionPage />)
    fireEvent.click(button('simulate error'))

    const controls = within(button('Start session').parentElement as HTMLElement)
    for (const control of controls.getAllByRole('button')) {
      expect(control).toBeDisabled()
    }

    fireEvent.click(button('clear'))
    expect(badge()).toHaveTextContent('Ready')
    expect(button('Start session')).toBeEnabled()
  })
})
