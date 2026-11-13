import { useEffect, useId, useState } from 'react'
import CalibrationSlider from './CalibrationSlider'
import type { CalibrationKey } from './calibrationSettings'
import {
  CALIBRATION_CONTROLS,
  DEFAULT_CALIBRATION,
  fetchCalibration,
  saveCalibration,
} from './calibrationSettings'

type SaveStatus = 'saved' | 'reset' | 'error' | null

const statusMessages: Record<'saved' | 'reset', string> = {
  saved: 'Calibration saved.',
  reset: 'Calibration reset to defaults.',
}

function GestureCalibrationSection() {
  const headingId = useId()
  const [settings, setSettings] = useState(DEFAULT_CALIBRATION)
  const [offline, setOffline] = useState(false)
  const [status, setStatus] = useState<SaveStatus>(null)

  useEffect(() => {
    let cancelled = false
    void fetchCalibration().then((loaded) => {
      if (cancelled) return
      if (loaded) setSettings(loaded)
      setOffline(!loaded)
    })
    return () => {
      cancelled = true
    }
  }, [])

  function handleChange(key: CalibrationKey, value: number) {
    setSettings((current) => ({ ...current, [key]: value }))
    setStatus(null)
  }

  async function handleSave() {
    setStatus((await saveCalibration(settings)) ? 'saved' : 'error')
  }

  async function handleReset() {
    if (await saveCalibration(DEFAULT_CALIBRATION)) {
      setSettings(DEFAULT_CALIBRATION)
      setStatus('reset')
    } else {
      setStatus('error')
    }
  }

  return (
    <section className="calibration-section" aria-labelledby={headingId}>
      <h2 id={headingId}>Gesture Calibration</h2>
      <p className="calibration-intro">
        Adjust how SlideKick recognizes your swipes. Saved settings apply right
        away, even during a session.
      </p>
      {offline && (
        <p className="calibration-note">
          Can't reach SlideKick, so these are the default settings. Start
          SlideKick to load and save your calibration.
        </p>
      )}

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
