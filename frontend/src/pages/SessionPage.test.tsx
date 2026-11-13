import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import SessionPage from './SessionPage'

function button(name: string) {
  return screen.getByRole('button', { name })
}

function badge() {
  return screen.getByText(/^(Session starting|Ready|Active|Paused|Ended|Error)$/)
}

async function expectBadge(text: string) {
  await waitFor(() => expect(badge()).toHaveTextContent(text))
}

async function renderPage(expected = 'Ready') {
  render(<SessionPage />)
  await expectBadge(expected)
}

async function click(name: string, expected: string) {
  fireEvent.click(button(name))
  await expectBadge(expected)
}

describe('SessionPage', () => {
  it('shows Session starting until SlideKick replies', async () => {
    render(<SessionPage />)
    expect(badge()).toHaveTextContent('Session starting')
    expect(screen.getByText('Presentation: Connecting')).toBeInTheDocument()
    await expectBadge('Ready')
  })

  it('renders the Ready state from the backend', async () => {
    await renderPage()
    expect(screen.getByText('Presentation: Connected')).toBeInTheDocument()
    expect(button('Start session')).toBeEnabled()
  })

  it('shows Session starting while the camera starts', async () => {
    fakeBackend.camera = 'starting'
    await renderPage('Session starting')
    expect(screen.getByText('Starting camera...')).toBeInTheDocument()
  })

  it('shows camera unavailable when the camera failed', async () => {
    fakeBackend.camera = 'error'
    await renderPage('Error')
    expect(screen.getByText('No camera source is available.')).toBeInTheDocument()
    expect(button('Start session')).toBeDisabled()
  })

  it('shows how to start SlideKick when it cannot be reached', async () => {
    fakeBackend.online = false
    await renderPage('Error')
    expect(screen.getByText(/Can't reach SlideKick/)).toBeInTheDocument()
    expect(screen.getByText('Presentation: Disconnected')).toBeInTheDocument()
  })

  it('shows a presentation error from the backend', async () => {
    fakeBackend.presentationError = 'Presentation command failed: boom'
    await renderPage()
    expect(screen.getByText('Presentation: Error')).toBeInTheDocument()
    expect(screen.getByText('Presentation command failed: boom')).toBeInTheDocument()
  })

  it('shows recognized gestures with confidence', async () => {
    await renderPage()
    await click('Start session', 'Active')

    fakeBackend.emitGesture('next', 0.92)

    expect(await screen.findByText('92% confidence')).toBeInTheDocument()
    expect(screen.getAllByText('Next').length).toBeGreaterThan(0)
  })

  it('treats no gesture as a normal state, not an error', async () => {
    await renderPage()
    await click('Start session', 'Active')
    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
  })

  it('walks through start, pause, resume, and end', async () => {
    await renderPage()

    await click('Start session', 'Active')
    expect(button('End session')).toBeEnabled()

    await click('Pause session', 'Paused')
    // The session state model doesn't allow ending while paused.
    expect(button('End session')).toBeDisabled()

    await click('Resume session', 'Active')
    expect(button('End session')).toBeEnabled()

    await click('End session', 'Ended')
    expect(button('Start new session')).toBeEnabled()
    expect(button('Pause session')).toBeDisabled()
    expect(screen.getByText('Camera off')).toBeInTheDocument()
  })

  it('shows a message for each session state', async () => {
    await renderPage()

    await click('Start session', 'Active')
    expect(
      screen.getByText('Gesture recognition is on. Gestures will control your presentation.'),
    ).toBeInTheDocument()

    await click('Pause session', 'Paused')
    expect(
      screen.getByText('Gesture recognition paused. Gestures will not control your presentation.'),
    ).toBeInTheDocument()

    await click('Resume session', 'Active')
    await click('End session', 'Ended')
    expect(
      screen.getByText("Session ended. Start a new session when you're ready."),
    ).toBeInTheDocument()
  })

  it('does not show gestures while paused', async () => {
    fakeBackend.state = 'paused'
    fakeBackend.emitGesture('next', 0.92)
    await renderPage('Paused')

    expect(screen.getByText('Gesture recognition paused')).toBeInTheDocument()
    expect(screen.queryByText('Next')).not.toBeInTheDocument()
    expect(screen.queryByText('92% confidence')).not.toBeInTheDocument()
  })

  it('clears the last gesture after pausing and resuming', async () => {
    await renderPage()
    await click('Start session', 'Active')
    fakeBackend.emitGesture('next', 0.92)
    expect(await screen.findByText('92% confidence')).toBeInTheDocument()

    await click('Pause session', 'Paused')
    await click('Resume session', 'Active')

    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
    expect(screen.queryByText('92% confidence')).not.toBeInTheDocument()
  })

  it('can start a new session after ending', async () => {
    await renderPage()
    await click('Start session', 'Active')
    await click('End session', 'Ended')

    await click('Start new session', 'Active')
    expect(button('End session')).toBeEnabled()
  })

  it('disables session controls during an error and recovers', async () => {
    fakeBackend.online = false
    await renderPage('Error')

    const controls = within(button('Start session').parentElement as HTMLElement)
    for (const control of controls.getAllByRole('button')) {
      expect(control).toBeDisabled()
    }

    fakeBackend.online = true
    await expectBadge('Ready')
    expect(button('Start session')).toBeEnabled()
  })
})
