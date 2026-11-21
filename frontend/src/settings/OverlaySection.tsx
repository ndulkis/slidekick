import { useEffect, useState } from 'react'
import { api } from '../core/api'
import type { OverlayPosition, OverlaySettings } from '../session/types'
import { overlayPositionLabels, overlayPositions } from '../session/types'

/** Turns the presentation overlay on or off and picks its screen corner.
 * Changes save right away and reach the overlay within a poll, even mid-session. */
function OverlaySection() {
  const [overlay, setOverlay] = useState<OverlaySettings | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    api<OverlaySettings>('/overlay').then(
      (res) => {
        if (!cancelled && res.ok) setOverlay(res.body)
      },
      () => {
        if (!cancelled) setError('Unable to load the overlay settings.')
      },
    )
    return () => {
      cancelled = true
    }
  }, [])

  async function save(next: OverlaySettings) {
    const previous = overlay
    setOverlay(next)
    setError('')
    try {
      const res = await api<OverlaySettings>('/overlay', 'PUT', next)
      if (res.ok) return setOverlay(res.body)
    } catch {
      // Falls through to the error below.
    }
    setOverlay(previous)
    setError("Couldn't save the overlay settings. Try again.")
  }

  return (
    <section className="calibration-section" aria-labelledby="overlay-settings-title">
      <h2 id="overlay-settings-title">Presentation overlay</h2>
      <p className="calibration-intro">
        A small badge over your slides that shows the session status and confirms each
        recognized gesture.
      </p>

      <label className="overlay-toggle">
        <input
          type="checkbox"
          checked={overlay?.enabled ?? false}
          disabled={!overlay}
          onChange={(e) => overlay && void save({ ...overlay, enabled: e.target.checked })}
        />
        Show the overlay during presentations
      </label>

      <fieldset className="overlay-positions" disabled={!overlay?.enabled}>
        <legend>Position on screen</legend>
        {overlayPositions.map((position: OverlayPosition) => (
          <label key={position}>
            <input
              type="radio"
              name="overlay-position"
              value={position}
              checked={overlay?.position === position}
              onChange={() => overlay && void save({ ...overlay, position })}
            />
            {overlayPositionLabels[position]}
          </label>
        ))}
      </fieldset>

      {error && (
        <p className="calibration-error" role="alert">
          {error}
        </p>
      )}
    </section>
  )
}

export default OverlaySection
