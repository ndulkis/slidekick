import GestureCalibrationSection from '../settings/GestureCalibrationSection'
import './SettingsPage.css'

function SettingsPage() {
  return (
    <section>
      <h1>Settings</h1>
      <p>
        Gesture mapping, camera selection, and presentation adapter
        configuration will live here.
      </p>

      <GestureCalibrationSection />
    </section>
  )
}

export default SettingsPage
