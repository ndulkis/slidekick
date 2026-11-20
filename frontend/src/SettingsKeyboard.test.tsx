import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'
import { DEFAULT_CALIBRATION } from './settings/calibrationSettings'
import { fakeBackend } from './test/fakeBackend'

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
  it('reaches every calibration control with Tab in order', async () => {
    const user = renderSettings()
    await screen.findByRole('combobox', { name: 'Camera' })

    await user.tab()
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Session' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Quit SlideKick' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('combobox', { name: 'Camera' })).toHaveFocus()

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

    expect(await screen.findByText('Calibration saved.')).toBeInTheDocument()
  })

  it('resets to the defaults with Space', async () => {
    fakeBackend.calibration.swipe_cooldown = 2.5
    const user = renderSettings()
    await waitFor(() => expect(slider('Time between gestures').value).toBe('2.5'))

    button('Reset to defaults').focus()
    await user.keyboard(' ')

    expect(await screen.findByText('Calibration reset to defaults.')).toBeInTheDocument()
    expect(slider('Time between gestures').value).toBe(String(DEFAULT_CALIBRATION.cooldown))
  })

  it('lets focus move on after the last control', async () => {
    const user = renderSettings()

    button('Reset to defaults').focus()
    await user.keyboard(' ')
    await user.tab()

    expect(button('Reset to defaults')).not.toHaveFocus()
  })
})

// Keyboard-only use of the Gesture Bindings section (SCRUM-95). jsdom doesn't
// open native dropdowns, so choosing an option uses selectOptions on the
// focused dropdown; arrow-key changes are covered by the manual walkthrough.

function dropdown(name: string) {
  return screen.getByRole('combobox', { name }) as HTMLSelectElement
}

async function renderBindings() {
  const user = renderSettings()
  await waitFor(() => expect(dropdown('Swipe right')).toBeEnabled())
  return user
}

describe('Settings gesture bindings keyboard use', () => {
  it('reaches every binding control with Tab after calibration', async () => {
    const user = await renderBindings()

    button('Reset to defaults').focus()
    await user.tab()
    expect(dropdown('Swipe left')).toHaveFocus()
    await user.tab()
    expect(dropdown('Swipe right')).toHaveFocus()
    await user.tab()
    expect(button('Save bindings')).toHaveFocus()
    await user.tab()
    expect(button('Reset bindings to defaults')).toHaveFocus()
  })

  it('changes a binding and saves it with Enter', async () => {
    const user = await renderBindings()

    dropdown('Swipe right').focus()
    await user.selectOptions(dropdown('Swipe right'), 'Previous slide')
    expect(dropdown('Swipe right')).toHaveFocus()
    await user.tab()
    expect(button('Save bindings')).toHaveFocus()
    await user.keyboard('{Enter}')

    expect(await screen.findByText('Gesture bindings saved.')).toBeInTheDocument()
    expect(fakeBackend.bindings.swipe_right).toBe('previous')
  })

  it('resets the bindings to the defaults with Space', async () => {
    fakeBackend.bindings = { swipe_right: 'previous', swipe_left: 'next' }
    const user = await renderBindings()
    await waitFor(() => expect(dropdown('Swipe right').value).toBe('previous'))

    button('Reset bindings to defaults').focus()
    await user.keyboard(' ')

    expect(await screen.findByText('Gesture bindings reset to defaults.')).toBeInTheDocument()
    expect(dropdown('Swipe right').value).toBe('next')
    expect(dropdown('Swipe left').value).toBe('previous')
  })

  it('lets focus move on after the last binding control', async () => {
    const user = await renderBindings()

    button('Reset bindings to defaults').focus()
    await user.keyboard(' ')
    await screen.findByText('Gesture bindings reset to defaults.')
    await user.tab()

    expect(button('Reset bindings to defaults')).not.toHaveFocus()
  })
})
