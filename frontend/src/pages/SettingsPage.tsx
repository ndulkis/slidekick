import { useId } from 'react'
import CameraPicker from '../settings/CameraPicker'
import GestureBindingsSection from '../settings/GestureBindingsSection'
import GestureCalibrationSection from '../settings/GestureCalibrationSection'
import './SettingsPage.css'

function SettingsPage() {
  const cameraHeadingId = useId()

  return (
    <section>
      <h1>Settings</h1>

      <section className="calibration-section" aria-labelledby={cameraHeadingId}>
        <h2 id={cameraHeadingId}>Camera</h2>
        <p className="calibration-intro">
          The camera SlideKick watches for gestures. You can also switch it during a
          session.
        </p>
        <CameraPicker />
      </section>

      <GestureCalibrationSection />

      <GestureBindingsSection />
    </section>
  )
}

export default SettingsPage
