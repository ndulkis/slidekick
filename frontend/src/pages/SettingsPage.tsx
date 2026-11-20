import CameraPicker from '../settings/CameraPicker'
import GestureProfileSection from '../settings/GestureProfileSection'
import GestureBindingsSection from '../settings/GestureBindingsSection'
import GestureCalibrationSection from '../settings/GestureCalibrationSection'
import './SettingsPage.css'

function SettingsPage() {
  return (
    <section>
      <h1>Settings</h1>
      <p>Presentation adapter configuration will live here.</p>

      <CameraPicker />

      <GestureProfileSection />

      <GestureCalibrationSection />

      <GestureBindingsSection />
    </section>
  )
}

export default SettingsPage
