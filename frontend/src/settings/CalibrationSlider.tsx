import { useId } from 'react'
import type { CalibrationControl } from './calibrationSettings'

interface CalibrationSliderProps {
  control: CalibrationControl
  value: number
  onChange: (value: number) => void
}

// Rounds away float noise from range steps (e.g. 0.15000000000000002).
function displayValue(control: CalibrationControl, value: number) {
  return control.unit === '%' ? Math.round(value * 100) : Number(value.toFixed(2))
}

function CalibrationSlider({ control, value, onChange }: CalibrationSliderProps) {
  const id = useId()
  const inputId = `${id}-input`
  const descriptionId = `${id}-description`

  const shown = displayValue(control, value)
  const visibleValue = control.unit === '%' ? `${shown}%` : `${shown} s`
  const spokenValue = control.unit === '%' ? `${shown}%` : `${shown} seconds`

  return (
    <div className="calibration-slider">
      <div className="calibration-slider-header">
        <label htmlFor={inputId}>{control.label}</label>
        {/* Screen readers get the value from aria-valuetext instead. */}
        <span className="calibration-slider-value" aria-hidden="true">
          {visibleValue}
        </span>
      </div>
      <input
        id={inputId}
        type="range"
        min={control.min}
        max={control.max}
        step={control.step}
        value={value}
        aria-valuetext={spokenValue}
        aria-describedby={descriptionId}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <p id={descriptionId} className="calibration-slider-description">
        {control.description}
      </p>
    </div>
  )
}

export default CalibrationSlider
