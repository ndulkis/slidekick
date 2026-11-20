import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
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
    fakeBackend.cameraOnStart = 'starting'
    await renderPage()
    await click('Start session', 'Session starting')
    expect(screen.getByText('Starting camera...')).toBeInTheDocument()
    expect(button('End session')).toBeDisabled()

    fakeBackend.camera = 'ready'
    await expectBadge('Active')
  })

  it('lets the user retry when the camera failed to start', async () => {
    // The backend ends the session when the camera can't open.
    fakeBackend.state = 'ended'
    fakeBackend.camera = 'error'
    await renderPage('Ended')
    expect(screen.getByRole('alert')).toHaveTextContent("The camera couldn't start.")
    expect(screen.getByText('No camera source is available.')).toBeInTheDocument()

    await click('Start new session', 'Active')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
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

  it('switches cameras during a session and shows a failed switch', async () => {
    await renderPage()
    await click('Start session', 'Active')

    const picker = await screen.findByRole('combobox', { name: 'Camera' })
    fireEvent.change(picker, { target: { value: 'phone' } })
    await waitFor(() => expect(fakeBackend.selectedCamera).toBe('phone'))

    fakeBackend.failCameraSwitch = true
    fireEvent.change(picker, { target: { value: 'builtin' } })
    expect(await screen.findByRole('alert')).toHaveTextContent(
      "Couldn't switch to MacBook Pro Camera, still using iPhone Camera.",
    )
    expect(picker).toHaveValue('phone')
  })

  it('shows a loading screen while the new camera opens', async () => {
    await renderPage()
    await click('Start session', 'Active')

    fakeBackend.cameraSwitching = true
    expect(await screen.findByText('Switching camera...')).toBeInTheDocument()

    fakeBackend.cameraSwitching = false
    await waitFor(() => expect(screen.queryByText('Switching camera...')).toBeNull())
  })

  it('hides the camera picker when there is only one camera', async () => {
    fakeBackend.cameras = [{ id: 'default', name: 'Default camera' }]
    await renderPage()
    await waitFor(() => expect(screen.queryByRole('combobox', { name: 'Camera' })).toBeNull())
  })

  it('gives Windows camera privacy advice when the camera fails', async () => {
    vi.spyOn(navigator, 'userAgent', 'get').mockReturnValue('Mozilla/5.0 (Windows NT 10.0)')
    fakeBackend.state = 'ended'
    fakeBackend.camera = 'error'
    await renderPage('Ended')
    expect(screen.getByRole('alert')).toHaveTextContent('Let desktop apps access your camera')
    vi.restoreAllMocks()
  })

  it('disables the camera picker while the camera starts', async () => {
    fakeBackend.cameraOnStart = 'starting'
    await renderPage()
    await click('Start session', 'Session starting')
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Camera' })).toBeDisabled())
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
