import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'
import { CALIBRATION_CONTROLS } from './settings/calibrationSettings'
import { fakeBackend } from './test/fakeBackend'

// Accessibility checks for the Gesture Calibration section (SCRUM-89),
// based on the WCAG findings in sprints/S4-R02-T1-Calibration-Accessibility-Research.md.

function renderSettings() {
  render(
    <MemoryRouter initialEntries={['/settings']}>
      <App />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

describe('Settings calibration accessibility', () => {
  it('uses a logical heading structure', () => {
    renderSettings()
    expect(screen.getByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { level: 2, name: 'Gesture Calibration' }),
    ).toBeInTheDocument()
  })

  it('gives every slider a label, description, and readable value', () => {
    renderSettings()
    for (const control of CALIBRATION_CONTROLS) {
      const slider = screen.getByRole('slider', { name: control.label })
      expect(slider).toHaveAccessibleDescription(control.description)
      expect(slider.getAttribute('aria-valuetext')).toMatch(/^\d+(\.\d+)?(%| seconds)$/)
    }
  })

  it('has the status region in place before anything is announced', () => {
    renderSettings()
    const section = screen.getByRole('region', { name: 'Gesture Calibration' })
    const status = within(section).getByRole('status')
    expect(status).toBeEmptyDOMElement()
  })

  it('raises an alert when SlideKick refuses the calibration', async () => {
    fakeBackend.rejectCalibration = true
    const user = renderSettings()

    await user.click(screen.getByRole('button', { name: 'Save calibration' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      "Your calibration couldn't be saved. Try again. Your previous settings are still in use.",
    )
  })

  it('tells users when SlideKick is not running', async () => {
    fakeBackend.online = false
    renderSettings()
    expect(await screen.findByText(/Can't reach SlideKick/)).toBeInTheDocument()
  })
})

// Accessibility checks for the Gesture Bindings section (SCRUM-95), using the
// same WCAG checks as the calibration section above.

function bindingsSection() {
  return screen.getByRole('region', { name: 'Gesture Bindings' })
}

async function renderBindings() {
  const user = renderSettings()
  await waitFor(() => expect(screen.getByRole('combobox', { name: 'Swipe right' })).toBeEnabled())
  return user
}

describe('Settings gesture bindings accessibility', () => {
  it('is a labelled region with its own heading under the page heading', () => {
    renderSettings()
    expect(screen.getByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument()
    expect(
      within(bindingsSection()).getByRole('heading', { level: 2, name: 'Gesture Bindings' }),
    ).toBeInTheDocument()
  })

  it('labels every dropdown and gives each reset button its own name', async () => {
    await renderBindings()
    const [left, right] = within(bindingsSection()).getAllByRole('combobox')
    expect(left).toHaveAccessibleName('Swipe left')
    expect(right).toHaveAccessibleName('Swipe right')

    const resets = screen.getAllByRole('button', { name: /reset/i }).map((b) => b.textContent)
    expect(resets).toEqual(['Reset to defaults', 'Reset bindings to defaults'])
  })

  it('never offers ending the session as a gesture command', async () => {
    await renderBindings()
    const section = bindingsSection()
    for (const dropdown of within(section).getAllByRole('combobox')) {
      const options = within(dropdown)
        .getAllByRole('option')
        .map((o) => o.textContent)
      expect(options).toEqual(['Next slide', 'Pause slideshow', 'Previous slide', 'Resume slideshow'])
    }
    expect(within(section).getByText(/Ending a session is always a button/)).toBeInTheDocument()
  })

  it('has the status region in place before anything is announced', async () => {
    const user = await renderBindings()
    const status = within(bindingsSection()).getByRole('status')
    expect(status).toBeEmptyDOMElement()

    await user.click(screen.getByRole('button', { name: 'Save bindings' }))

    await waitFor(() => expect(status).toHaveTextContent('Gesture bindings saved.'))
  })

  it('raises an alert with the reason when SlideKick refuses the bindings', async () => {
    const user = await renderBindings()
    // The page never offers "end"; add it here to make the backend refuse.
    const dropdown = screen.getByRole('combobox', { name: 'Swipe left' }) as HTMLSelectElement
    dropdown.append(new Option('End session', 'end'))
    await user.selectOptions(dropdown, 'end')

    await user.click(screen.getByRole('button', { name: 'Save bindings' }))

    const alert = await within(bindingsSection()).findByRole('alert')
    expect(alert).toHaveTextContent(/not a bindable command/)
    expect(alert).toHaveTextContent('Your previous bindings are still in use.')
  })

  it('tells users when SlideKick is not running and disables the controls', async () => {
    fakeBackend.online = false
    renderSettings()

    expect(await screen.findByText(/SlideKick isn't running/)).toBeInTheDocument()
    const section = bindingsSection()
    for (const control of [
      ...within(section).getAllByRole('combobox'),
      ...within(section).getAllByRole('button'),
    ]) {
      expect(control).toBeDisabled()
    }
  })
})
