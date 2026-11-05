import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import GestureCalibrationSection from './GestureCalibrationSection'
import { CALIBRATION_STORAGE_KEY, DEFAULT_CALIBRATION } from './calibrationSettings'

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial))
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value)
    },
    removeItem: (key: string) => {
      data.delete(key)
    },
  }
}

function failingStorage() {
  return {
    getItem: () => null,
    setItem: () => {
      throw new Error('quota exceeded')
    },
    removeItem: () => {},
  }
}

function slider(name: string) {
  return screen.getByLabelText(name) as HTMLInputElement
}

describe('GestureCalibrationSection', () => {
  it('shows the four calibration sliders with the defaults', () => {
    render(<GestureCalibrationSection storage={memoryStorage()} />)

    expect(screen.getByRole('heading', { name: 'Gesture Calibration' })).toBeInTheDocument()
    expect(screen.getAllByRole('slider')).toHaveLength(4)
    expect(slider('Swipe distance').value).toBe(String(DEFAULT_CALIBRATION.swipeDistance))
    expect(slider('Time between gestures').value).toBe(String(DEFAULT_CALIBRATION.cooldown))
  })

  it('says the settings are not applied to recognition yet', () => {
    render(<GestureCalibrationSection storage={memoryStorage()} />)
    expect(
      screen.getByText(/these settings aren't applied to gesture recognition yet/),
    ).toBeInTheDocument()
  })

  it('loads a saved profile', () => {
    const storage = memoryStorage({
      [CALIBRATION_STORAGE_KEY]: JSON.stringify({ ...DEFAULT_CALIBRATION, cooldown: 2.5 }),
    })
    render(<GestureCalibrationSection storage={storage} />)

    expect(slider('Time between gestures').value).toBe('2.5')
  })

  it('saves changes and announces it', () => {
    const storage = memoryStorage()
    render(<GestureCalibrationSection storage={storage} />)

    fireEvent.change(slider('Swipe distance'), { target: { value: '0.15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save calibration' }))

    expect(screen.getByRole('status')).toHaveTextContent('Calibration saved.')
    expect(JSON.parse(storage.getItem(CALIBRATION_STORAGE_KEY)!)).toMatchObject({
      swipeDistance: 0.15,
    })
  })

  it('resets to the defaults and announces it', () => {
    const storage = memoryStorage({
      [CALIBRATION_STORAGE_KEY]: JSON.stringify({ ...DEFAULT_CALIBRATION, cooldown: 2.5 }),
    })
    render(<GestureCalibrationSection storage={storage} />)

    fireEvent.click(screen.getByRole('button', { name: 'Reset to defaults' }))

    expect(slider('Time between gestures').value).toBe(String(DEFAULT_CALIBRATION.cooldown))
    expect(screen.getByRole('status')).toHaveTextContent('Calibration reset to defaults.')
    expect(storage.getItem(CALIBRATION_STORAGE_KEY)).toBeNull()
  })

  it('shows an alert when saving fails', () => {
    render(<GestureCalibrationSection storage={failingStorage()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Save calibration' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      "Your calibration couldn't be saved. Try again. Your previous settings are still in use.",
    )
    expect(screen.getByRole('status')).toHaveTextContent('')
  })

  it('clears the last message when a setting changes', () => {
    render(<GestureCalibrationSection storage={memoryStorage()} />)
    fireEvent.click(screen.getByRole('button', { name: 'Save calibration' }))

    fireEvent.change(slider('Recognition strictness'), { target: { value: '0.7' } })

    expect(screen.getByRole('status')).toHaveTextContent('')
  })
})
