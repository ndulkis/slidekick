import CameraPicker from '../settings/CameraPicker'
import GestureProfileSection from '../settings/GestureProfileSection'
import GestureCalibrationSection from '../settings/GestureCalibrationSection'
import './SettingsPage.css'

function SettingsPage() {
  return (
    <section>
      <h1>Settings</h1>
      <p>
        Gesture mapping and presentation adapter configuration will live
        here.
      </p>

      <CameraPicker />

      <GestureProfileSection />

      <GestureCalibrationSection />
    </section>
  )
}

export default SettingsPage
