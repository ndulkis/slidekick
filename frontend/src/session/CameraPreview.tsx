import cameraOffIcon from '../assets/robot/camera-off.svg'
import errorIcon from '../assets/robot/error.svg'
import loadingIcon from '../assets/robot/loading.svg'
import type { SessionStatus } from './types'

interface CameraPreviewProps {
  status: SessionStatus
  hasCamera: boolean
}

function CameraPreview({ status, hasCamera }: CameraPreviewProps) {
  if (!hasCamera) {
    return (
      <div className="camera-preview camera-preview-empty" role="status">
        <img src={errorIcon} alt="" />
        No camera source is available.
      </div>
    )
  }

  if (status === 'loading') {
    return (
      <div className="camera-preview camera-preview-loading" role="status">
        <img src={loadingIcon} alt="" />
        Starting camera...
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="camera-preview camera-preview-error" role="alert">
        <img src={errorIcon} alt="" />
        Camera not available. Check camera access and try again.
      </div>
    )
  }

  // The camera only runs during a session: it is off before the first start
  // and again once the session has ended.
  if (status === 'ready' || status === 'ended') {
    return (
      <div className={`camera-preview camera-preview-${status}`} role="status">
        <img src={cameraOffIcon} alt="" />
        Camera off
      </div>
    )
  }

  const label = status === 'paused' ? 'Camera preview (paused)' : 'Camera preview'

  // The backend streams the camera as MJPEG, which an <img> plays natively.
  // It is only mounted during a session, so each session opens a new stream.
  return (
    <div className={`camera-preview camera-preview-live camera-preview-${status}`}>
      <img src="/api/camera" alt={label} />
    </div>
  )
}

export default CameraPreview
