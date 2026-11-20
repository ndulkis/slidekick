import { useEffect, useId, useState } from 'react'
import type { Bindings, BindingsInfo, SaveResult } from './gestureBindings'
import {
  DEFAULT_BINDINGS,
  commandLabel,
  fetchBindings,
  gestureLabel,
  resetBindings,
  saveBindings,
} from './gestureBindings'

type Status = 'saved' | 'reset' | null

const statusMessages: Record<'saved' | 'reset', string> = {
  saved: 'Gesture bindings saved.',
  reset: 'Gesture bindings reset to defaults.',
}

function GestureBindingsSection() {
  const headingId = useId()
  const [info, setInfo] = useState<BindingsInfo | undefined>(undefined)
  const [draft, setDraft] = useState<Bindings>(DEFAULT_BINDINGS)
  const [offline, setOffline] = useState(false)
  const [status, setStatus] = useState<Status>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void fetchBindings().then((loaded) => {
      if (cancelled) return
      if (loaded) {
        setInfo(loaded)
        setDraft(loaded.bindings)
      }
      setOffline(!loaded)
    })
    return () => {
      cancelled = true
    }
  }, [])

  function handleChange(gesture: string, command: string) {
    setDraft((current) => ({ ...current, [gesture]: command }))
    setStatus(null)
    setError(null)
  }

  function apply(result: SaveResult, done: 'saved' | 'reset') {
    if (result.ok) {
      setInfo(result.info)
      setDraft(result.info.bindings)
      setStatus(done)
      setError(null)
    } else {
      // The previous bindings are still active on the backend.
      setStatus(null)
      setError(result.error)
    }
  }

  const gestures = info?.gestures ?? Object.keys(DEFAULT_BINDINGS)
  const commands = info?.bindableCommands ?? ['next', 'previous']
  const disabled = !info

  return (
    <section className="calibration-section" aria-labelledby={headingId}>
      <h2 id={headingId}>Gesture Bindings</h2>
      <p className="calibration-intro">
        Choose what each gesture does during a presentation. Saved bindings
        apply right away.
      </p>
      <p className="calibration-note">
        Ending a session is always a button on the Session page, never a
        gesture, so a stray movement can't close your slideshow.
      </p>
      {offline && (
        <p className="calibration-note">
          SlideKick isn't running, so your gesture bindings can't be shown.
          Start SlideKick to view and change them.
        </p>
      )}

      {gestures.map((gesture) => {
        const selectId = `${headingId}-${gesture}`
        return (
          <div className="binding-row" key={gesture}>
            <label htmlFor={selectId}>{gestureLabel(gesture)}</label>
            <select
              id={selectId}
              value={draft[gesture] ?? ''}
              disabled={disabled}
              onChange={(event) => handleChange(gesture, event.target.value)}
            >
              {draft[gesture] === undefined && <option value="">Not bound</option>}
              {commands.map((command) => (
                <option key={command} value={command}>
                  {commandLabel(command)}
                </option>
              ))}
            </select>
          </div>
        )
      })}

      <div className="calibration-actions">
        <button
          type="button"
          disabled={disabled}
          onClick={async () => apply(await saveBindings(draft), 'saved')}
        >
          Save bindings
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={async () => apply(await resetBindings(), 'reset')}
        >
          Reset bindings to defaults
        </button>
      </div>

      {/* Always rendered so screen readers announce changes to it. */}
      <p className="calibration-status" role="status">
        {status ? statusMessages[status] : ''}
      </p>

      {error && (
        <p className="calibration-error" role="alert">
          {error} Your previous bindings are still in use.
        </p>
      )}
    </section>
  )
}

export default GestureBindingsSection
