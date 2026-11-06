import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { CALIBRATION_CONTROLS } from './settings/calibrationSettings'

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
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

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

  it('raises an alert when the browser blocks saving', async () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('storage blocked')
    })
    const user = renderSettings()

    await user.click(screen.getByRole('button', { name: 'Save calibration' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      "Your calibration couldn't be saved. Try again. Your previous settings are still in use.",
    )
  })

  it('tells users the settings are not applied to recognition yet', () => {
    renderSettings()
    expect(
      screen.getByText(/these settings aren't applied to gesture recognition yet/),
    ).toBeInTheDocument()
  })
})
