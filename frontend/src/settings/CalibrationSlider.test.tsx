import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import CalibrationSlider from './CalibrationSlider'
import { CALIBRATION_CONTROLS } from './calibrationSettings'

const distance = CALIBRATION_CONTROLS.find((c) => c.key === 'swipeDistance')!
const duration = CALIBRATION_CONTROLS.find((c) => c.key === 'swipeDuration')!

describe('CalibrationSlider', () => {
  it('renders a range input labelled by the control name', () => {
    render(<CalibrationSlider control={distance} value={0.1} onChange={vi.fn()} />)
    const slider = screen.getByLabelText('Swipe distance')
    expect(slider).toHaveAttribute('type', 'range')
  })

  it('links the description to the slider', () => {
    render(<CalibrationSlider control={distance} value={0.1} onChange={vi.fn()} />)
    expect(screen.getByLabelText('Swipe distance')).toHaveAccessibleDescription(
      distance.description,
    )
  })

  it('shows and announces percentage values', () => {
    render(<CalibrationSlider control={distance} value={0.1} onChange={vi.fn()} />)
    expect(screen.getByText('10%')).toBeInTheDocument()
    expect(screen.getByLabelText('Swipe distance')).toHaveAttribute('aria-valuetext', '10%')
  })

  it('shows and announces seconds values', () => {
    render(<CalibrationSlider control={duration} value={1.75} onChange={vi.fn()} />)
    expect(screen.getByText('1.75 s')).toBeInTheDocument()
    expect(screen.getByLabelText('Slowest allowed swipe')).toHaveAttribute(
      'aria-valuetext',
      '1.75 seconds',
    )
  })

  it('rounds float noise from range steps', () => {
    render(
      <CalibrationSlider control={distance} value={0.15000000000000002} onChange={vi.fn()} />,
    )
    expect(screen.getByText('15%')).toBeInTheDocument()
  })

  it('uses the control range and step', () => {
    render(<CalibrationSlider control={duration} value={1.75} onChange={vi.fn()} />)
    const slider = screen.getByLabelText('Slowest allowed swipe')
    expect(slider).toHaveAttribute('min', '1.25')
    expect(slider).toHaveAttribute('max', '3')
    expect(slider).toHaveAttribute('step', '0.25')
  })

  it('calls onChange with the new number', () => {
    const onChange = vi.fn()
    render(<CalibrationSlider control={distance} value={0.1} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Swipe distance'), { target: { value: '0.15' } })

    expect(onChange).toHaveBeenCalledWith(0.15)
  })
})
