import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

// Automated version of the SCRUM-85 usability walkthrough tasks (TC-01 to
// TC-07). Renders the whole app and drives it the way a user would.

function renderApp(path = '/') {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

function button(name: string) {
  return screen.getByRole('button', { name })
}

describe('Session workflow', () => {
  it('TC-01: navigates from the Dashboard to the Session page', async () => {
    const user = renderApp('/')

    await user.click(screen.getByRole('link', { name: 'Session' }))

    expect(screen.getByRole('heading', { name: 'Presentation Session' })).toBeInTheDocument()
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(button('Start session')).toBeEnabled()
  })

  it('TC-02 to TC-05: runs a full session from start to end', async () => {
    const user = renderApp('/session')

    // TC-02: Start
    await user.click(button('Start session'))
    expect(screen.getByText('Active')).toBeInTheDocument()
    await user.click(button('next'))
    expect(screen.getByText('92% confidence')).toBeInTheDocument()

    // TC-03: Pause hides gesture feedback
    await user.click(button('Pause session'))
    expect(screen.getByText('Paused')).toBeInTheDocument()
    expect(screen.getByText('Gesture recognition paused')).toBeInTheDocument()
    expect(screen.queryByText('92% confidence')).not.toBeInTheDocument()

    // TC-04: Resume
    await user.click(button('Resume session'))
    expect(screen.getByText('Active')).toBeInTheDocument()

    // TC-05: End
    await user.click(button('End session'))
    expect(screen.getByText('Ended')).toBeInTheDocument()
    expect(screen.getByText('Camera off')).toBeInTheDocument()
    expect(button('Start new session')).toBeEnabled()
  })

  it('TC-06: does not end the session while paused', async () => {
    const user = renderApp('/session')
    await user.click(button('Start session'))
    await user.click(button('Pause session'))

    expect(button('End session')).toBeDisabled()
    await user.click(button('End session'))

    expect(screen.getByText('Paused')).toBeInTheDocument()
    expect(screen.queryByText('Ended')).not.toBeInTheDocument()
  })

  it('TC-07: shows an error message and recovers when cleared', async () => {
    const user = renderApp('/session')

    await user.click(button('simulate error'))
    expect(
      screen.getByText(
        'Something required by this session is unavailable. Check camera access and try again.',
      ),
    ).toBeInTheDocument()
    expect(button('Start session')).toBeDisabled()

    await user.click(button('clear'))
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(button('Start session')).toBeEnabled()
  })
})
