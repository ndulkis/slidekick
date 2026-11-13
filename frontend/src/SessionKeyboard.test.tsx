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

async function renderReadySession() {
  const user = renderSession()
  await screen.findByText('Ready')
  return user
}

function button(name: string) {
  return screen.getByRole('button', { name })
}

describe('Session keyboard use (TC-08)', () => {
  it('reaches Start session after the nav links and starts with Enter', async () => {
    const user = await renderReadySession()

    await user.tab()
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Session' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Quit SlideKick' })).toHaveFocus()
    // End and Pause are disabled at Ready, so Start is the next stop.
    await user.tab()
    expect(button('Start session')).toHaveFocus()

    await user.keyboard('{Enter}')
    expect(await screen.findByText('Active')).toBeInTheDocument()
  })

  it('runs a full session with only the keyboard', async () => {
    const user = await renderReadySession()

    button('Start session').focus()
    await user.keyboard('{Enter}')
    expect(await screen.findByText('Active')).toBeInTheDocument()

    button('Pause session').focus()
    await user.keyboard(' ')
    expect(await screen.findByText('Paused')).toBeInTheDocument()

    button('Resume session').focus()
    await user.keyboard(' ')
    expect(await screen.findByText('Active')).toBeInTheDocument()

    button('End session').focus()
    await user.keyboard('{Enter}')
    expect(await screen.findByText('Ended')).toBeInTheDocument()
    expect(button('Start new session')).toBeEnabled()
  })

  it('skips the disabled End button while paused', async () => {
    const user = await renderReadySession()
    button('Start session').focus()
    await user.keyboard('{Enter}')
    button('Pause session').focus()
    await user.keyboard(' ')

    // From the header's last control, Tab skips the disabled Start and End buttons.
    button('Quit SlideKick').focus()
    await user.tab()

    expect(button('Resume session')).toHaveFocus()
    expect(button('End session')).toBeDisabled()
  })
})
