import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import { CALIBRATION_STORAGE_KEY, DEFAULT_CALIBRATION } from './settings/calibrationSettings'

// Keyboard-only use of the Gesture Calibration section (SCRUM-89).
// jsdom doesn't move native range inputs with the arrow keys, so changing a
// slider by keyboard is covered by the manual walkthrough instead.

function renderSettings() {
  render(
    <MemoryRouter initialEntries={['/settings']}>
      <App />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

function slider(name: string) {
  return screen.getByLabelText(name) as HTMLInputElement
}

function button(name: string) {
  return screen.getByRole('button', { name })
}

describe('Settings calibration keyboard use', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('reaches every calibration control with Tab in order', async () => {
    const user = renderSettings()

    await user.tab()
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Session' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveFocus()

    for (const name of [
      'Swipe distance',
      'Slowest allowed swipe',
      'Recognition strictness',
      'Time between gestures',
    ]) {
      await user.tab()
      expect(slider(name)).toHaveFocus()
    }

    await user.tab()
    expect(button('Save calibration')).toHaveFocus()
    await user.tab()
    expect(button('Reset to defaults')).toHaveFocus()
  })

  it('saves with Enter', async () => {
    const user = renderSettings()

    button('Save calibration').focus()
    await user.keyboard('{Enter}')

    expect(screen.getByRole('status')).toHaveTextContent('Calibration saved.')
    expect(localStorage.getItem(CALIBRATION_STORAGE_KEY)).not.toBeNull()
  })

  it('resets to the defaults with Space', async () => {
    localStorage.setItem(
      CALIBRATION_STORAGE_KEY,
      JSON.stringify({ ...DEFAULT_CALIBRATION, cooldown: 2.5 }),
    )
    const user = renderSettings()
    expect(slider('Time between gestures').value).toBe('2.5')

    button('Reset to defaults').focus()
    await user.keyboard(' ')

    expect(slider('Time between gestures').value).toBe(String(DEFAULT_CALIBRATION.cooldown))
    expect(screen.getByRole('status')).toHaveTextContent('Calibration reset to defaults.')
  })

  it('lets focus move on after the last control', async () => {
    const user = renderSettings()

    button('Reset to defaults').focus()
    await user.keyboard(' ')
    await user.tab()

    expect(button('Reset to defaults')).not.toHaveFocus()
  })
})
