import type { SessionStatus } from './types'

interface CameraPreviewProps {
  status: SessionStatus
  hasCamera: boolean
}

function CameraPreview({ status, hasCamera }: CameraPreviewProps) {
  if (!hasCamera) {
    return (
      <div className="camera-preview camera-preview-empty" role="status">
        No camera source is available.
      </div>
    )
  }

  if (status === 'loading') {
    return (
      <div className="camera-preview camera-preview-loading" role="status">
        Starting camera...
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="camera-preview camera-preview-error" role="alert">
        Camera not available. Check camera access and try again.
      </div>
    )
  }

  // The camera only runs during a session: it is off before the first start
  // and again once the session has ended.
  if (status === 'ready' || status === 'ended') {
    return (
      <div className={`camera-preview camera-preview-${status}`} role="status">
        Camera off
      </div>
    )
  }

  const label = status === 'paused' ? 'Camera preview (paused)' : 'Camera preview'

  return (
    <div className={`camera-preview camera-preview-${status}`} role="status">
      {label}
    </div>
  )
}

export default CameraPreview
