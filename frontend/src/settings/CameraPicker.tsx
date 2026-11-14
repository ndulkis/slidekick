import { useEffect, useState } from 'react'
import { api } from '../core/api'

type Camera = { id: string; name: string }
type CamerasBody = { cameras: Camera[]; selected: string | null }

interface CameraPickerProps {
  disabled?: boolean
  /** The camera in use during a session. Without it, the saved choice. */
  selected?: string | null
}

/** Chooses the camera SlideKick uses. Works during a session too. */
function CameraPicker({ disabled = false, selected }: CameraPickerProps) {
  const [cameras, setCameras] = useState<CamerasBody | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    api<CamerasBody>('/cameras').then(
      (res) => {
        if (!cancelled && res.ok) setCameras(res.body)
      },
      // Offline: the Session page already says SlideKick can't be reached.
      () => {},
    )
    return () => {
      cancelled = true
    }
  }, [])

  if (!cameras?.cameras.length) return null

  async function handleChange(id: string) {
    setError(false)
    try {
      const res = await api<CamerasBody>('/cameras', 'PUT', { id })
      if (res.ok) setCameras(res.body)
      else setError(true)
    } catch {
      setError(true)
    }
  }

  return (
    <>
      <p className="camera-picker">
        <label>
          Camera{' '}
          <select
            value={(selected || cameras.selected) ?? ''}
            disabled={disabled}
            onChange={(e) => void handleChange(e.target.value)}
          >
            {cameras.cameras.map((camera) => (
              <option key={camera.id} value={camera.id}>
                {camera.name}
              </option>
            ))}
          </select>
        </label>
      </p>
      {error && (
        <p className="session-message" role="alert">
          Couldn't change the camera. Try again.
        </p>
      )}
    </>
  )
}

export default CameraPicker
