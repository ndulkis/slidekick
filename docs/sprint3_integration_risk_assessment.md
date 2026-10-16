# Sprint 3 Integration Risk Assessment (S3-R04-T1)

## 1. Current Architecture Overview
SlideKick utilizes a native Windows helper (`windows_helper.py`) that acts as a standalone HTTP entry point for presentation control. While the primary gesture recognition pipeline (`run_gesture_control.py`) connects directly to the `KeyboardPresentationAdapter`, the Flask helper provides an alternative network interface that translates `/next`, `/previous`, `/pause`, and `/resume` endpoint triggers into physical keystrokes using the `pyautogui` library. 

Because `pyautogui` simulates keystrokes at the operating system level, it acts blindly—it does not know which application is receiving the keys.

## 2. Integration Risk Register

| Risk | Likelihood | Severity | Potential Impact | Proposed Recovery / Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **Slideshow Loses Focus** | High | High | Keystrokes are sent to the wrong application (e.g., a browser or terminal), potentially causing unintended destructive actions. | Implement a pre-execution focus warning, or establish a manual recovery process requiring user intervention. |
| **Flask Helper Unavailable** | Low | High | Commands fail to reach the adapter entirely; the application appears unresponsive to gestures via HTTP. | Add a health-check endpoint and UI status indicators to notify the user immediately if the connection drops. |
| **Duplicate Gesture Commands** | Medium | Medium | A single continuous gesture is registered multiple times by the camera, causing rapid, unintended slide transitions. | Verify the existing `SWIPE_COOLDOWN` in `swipe_recognizer.py` before adding additional debounce logic. |
| **Platform Keybind Differences** | High | Medium | Standard keystrokes (like 'b' for pause) might behave differently across PowerPoint, Google Slides, Windows, or macOS. | Abstract the keystrokes into a platform-specific configuration dictionary rather than hardcoding them. |
| **Native Execution Errors** | Low | Medium | PyAutoGUI crashes or fails due to system permissions (e.g., strict antivirus blocking simulated inputs). | Catch native exceptions in the helper and surface them to the UI for clear user feedback. |
| **Pause/Resume State Mismatch** | Medium | Low | Sending a 'pause' command while already paused might unpause the presentation depending on the software's toggle behavior. | Track the current presentation state in the UI or session controller to prevent duplicate toggle commands. |

## 3. Windows-Specific Recovery Procedures
*   **Focus Loss Recovery:** If the presentation window loses focus, the user must manually click back into the presentation. Future iterations could explore the Windows API to programmatically force focus back to the target window.
*   **Port Conflicts:** If port 8000 is blocked by another Windows service, the Flask application will crash on startup. The helper currently hardcodes port 8000. A proposed improvement is to configure this port dynamically via the `.env` file to bypass conflicts.

## 4. Cross-Platform Considerations
*   **Permissions:** On macOS, simulated keyboard control may require Accessibility permissions, while screen-capture functionality may require additional Screen Recording permissions. This significantly complicates the initial setup process compared to Windows.
*   **Key Mappings:** While arrow keys are universal, presentation toggle keys vary. The adapter must remain modular to support macOS-specific keystrokes if the target OS changes in future sprints.

## 5. Recommendations for S3-R04-T2 (Command Hardening)
Based on this assessment, the following hardening tasks should be prioritized for S3-R04-T2:
1.  **Evaluate Existing Cooldown:** Verify whether the existing `SWIPE_COOLDOWN` mechanism in `swipe_recognizer.py` adequately prevents duplicate commands before implementing secondary debounce logic.
2.  **Connection Health Check:** Add a `/health` endpoint to the Flask helper so the frontend can verify the adapter is running.
3.  **Graceful Degradation:** If the helper returns a 500 status code, the application should temporarily disable gesture commands and display an error toast in the UI.