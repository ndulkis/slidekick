import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

// Automated version of the SCRUM-85 keyboard-only walkthrough task (TC-08).
// Focus visibility still has to be checked manually in a real browser.

function renderSession() {
  render(
    <MemoryRouter initialEntries={['/session']}>
      <App />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

function button(name: string) {
  return screen.getByRole('button', { name })
}

describe('Session keyboard use (TC-08)', () => {
  it('reaches Start session after the nav links and starts with Enter', async () => {
    const user = renderSession()

    await user.tab()
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Session' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveFocus()
    // End and Pause are disabled at Ready, so Start is the next stop.
    await user.tab()
    expect(button('Start session')).toHaveFocus()

    await user.keyboard('{Enter}')
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('runs a full session with only the keyboard', async () => {
    const user = renderSession()

    button('Start session').focus()
    await user.keyboard('{Enter}')
    expect(screen.getByText('Active')).toBeInTheDocument()

    button('Pause session').focus()
    await user.keyboard(' ')
    expect(screen.getByText('Paused')).toBeInTheDocument()

    button('Resume session').focus()
    await user.keyboard(' ')
    expect(screen.getByText('Active')).toBeInTheDocument()

    button('End session').focus()
    await user.keyboard('{Enter}')
    expect(screen.getByText('Ended')).toBeInTheDocument()
    expect(button('Start new session')).toBeEnabled()
  })

  it('skips the disabled End button while paused', async () => {
    const user = renderSession()
    button('Start session').focus()
    await user.keyboard('{Enter}')
    button('Pause session').focus()
    await user.keyboard(' ')

    // From Settings, Tab skips the disabled Start and End buttons.
    screen.getByRole('link', { name: 'Settings' }).focus()
    await user.tab()

    expect(button('Resume session')).toHaveFocus()
    expect(button('End session')).toBeDisabled()
  })
})
