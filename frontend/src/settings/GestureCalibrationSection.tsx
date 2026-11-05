import { useId, useState } from 'react'
import CalibrationSlider from './CalibrationSlider'
import type { CalibrationKey, CalibrationStorage } from './calibrationSettings'
import {
  CALIBRATION_CONTROLS,
  loadCalibration,
  resetCalibration,
  saveCalibration,
} from './calibrationSettings'

interface GestureCalibrationSectionProps {
  /** Overrides browser storage; used by tests. */
  storage?: CalibrationStorage
}

type SaveStatus = 'saved' | 'reset' | 'error' | null

const statusMessages: Record<'saved' | 'reset', string> = {
  saved: 'Calibration saved.',
  reset: 'Calibration reset to defaults.',
}

function GestureCalibrationSection({ storage }: GestureCalibrationSectionProps) {
  const headingId = useId()
  const [settings, setSettings] = useState(() => loadCalibration(storage))
  const [status, setStatus] = useState<SaveStatus>(null)

  function handleChange(key: CalibrationKey, value: number) {
    setSettings((current) => ({ ...current, [key]: value }))
    setStatus(null)
  }

  function handleSave() {
    setStatus(saveCalibration(settings, storage) ? 'saved' : 'error')
  }

  function handleReset() {
    setSettings(resetCalibration(storage))
    setStatus('reset')
  }

  return (
    <section className="calibration-section" aria-labelledby={headingId}>
      <h2 id={headingId}>Gesture Calibration</h2>
      <p className="calibration-intro">
        Adjust how SlideKick recognizes your swipes. Your settings are saved in
        this browser.
      </p>

      {CALIBRATION_CONTROLS.map((control) => (
        <CalibrationSlider
          key={control.key}
          control={control}
          value={settings[control.key]}
          onChange={(value) => handleChange(control.key, value)}
        />
      ))}

      <div className="calibration-actions">
        <button type="button" onClick={handleSave}>
          Save calibration
        </button>
        <button type="button" onClick={handleReset}>
          Reset to defaults
        </button>
      </div>

      {/* Always rendered so screen readers announce changes to it. */}
      <p className="calibration-status" role="status">
        {status === 'saved' || status === 'reset' ? statusMessages[status] : ''}
      </p>

      {status === 'error' && (
        <p className="calibration-error" role="alert">
          Your calibration couldn't be saved. Try again. Your previous settings
          are still in use.
        </p>
      )}
    </section>
  )
}

export default GestureCalibrationSection
