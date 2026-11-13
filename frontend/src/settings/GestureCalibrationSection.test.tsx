import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import GestureCalibrationSection from './GestureCalibrationSection'
import { DEFAULT_CALIBRATION } from './calibrationSettings'

function slider(name: string) {
  return screen.getByLabelText(name) as HTMLInputElement
}

function click(name: string) {
  fireEvent.click(screen.getByRole('button', { name }))
}

describe('GestureCalibrationSection', () => {
  it('shows the four calibration sliders with the defaults', () => {
    render(<GestureCalibrationSection />)

    expect(screen.getByRole('heading', { name: 'Gesture Calibration' })).toBeInTheDocument()
    expect(screen.getAllByRole('slider')).toHaveLength(4)
    expect(slider('Swipe distance').value).toBe(String(DEFAULT_CALIBRATION.swipeDistance))
    expect(slider('Time between gestures').value).toBe(String(DEFAULT_CALIBRATION.cooldown))
  })

  it('loads the calibration SlideKick is using', async () => {
    fakeBackend.calibration.swipe_cooldown = 2.5
    render(<GestureCalibrationSection />)

    await waitFor(() => expect(slider('Time between gestures').value).toBe('2.5'))
  })

  it('keeps the defaults and says so when SlideKick is not running', async () => {
    fakeBackend.online = false
    render(<GestureCalibrationSection />)

    expect(await screen.findByText(/Can't reach SlideKick/)).toBeInTheDocument()
    expect(slider('Swipe distance').value).toBe(String(DEFAULT_CALIBRATION.swipeDistance))
  })

  it('saves changes to SlideKick and announces it', async () => {
    render(<GestureCalibrationSection />)

    fireEvent.change(slider('Swipe distance'), { target: { value: '0.15' } })
    click('Save calibration')

    expect(await screen.findByText('Calibration saved.')).toBeInTheDocument()
    expect(fakeBackend.calibration.min_displacement).toBe(0.15)
  })

  it('resets SlideKick to the defaults and announces it', async () => {
    fakeBackend.calibration.swipe_cooldown = 2.5
    render(<GestureCalibrationSection />)
    await waitFor(() => expect(slider('Time between gestures').value).toBe('2.5'))

    click('Reset to defaults')

    expect(await screen.findByText('Calibration reset to defaults.')).toBeInTheDocument()
    expect(slider('Time between gestures').value).toBe(String(DEFAULT_CALIBRATION.cooldown))
    expect(fakeBackend.calibration.swipe_cooldown).toBe(DEFAULT_CALIBRATION.cooldown)
  })

  it('shows an alert when saving fails', async () => {
    fakeBackend.rejectCalibration = true
    render(<GestureCalibrationSection />)

    click('Save calibration')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      "Your calibration couldn't be saved. Try again. Your previous settings are still in use.",
    )
    expect(screen.getByRole('status')).toHaveTextContent('')
  })

  it('clears the last message when a setting changes', async () => {
    render(<GestureCalibrationSection />)
    click('Save calibration')
    await screen.findByText('Calibration saved.')

    fireEvent.change(slider('Recognition strictness'), { target: { value: '0.7' } })

    expect(screen.getByRole('status')).toHaveTextContent('')
  })
})
