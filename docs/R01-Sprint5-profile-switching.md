# R01 Sprint 5: Switch Between Gesture Profiles

This implementation adds **binding-only** switching between saved JSON profiles containing the recognized `swipe_left` and `swipe_right` gestures. It does **not** hot-swap MediaPipe custom models or implement the proposed R01/R03 atomic model-activation contract.

## Running

From the repository root, activate `.venv`, install the dependencies documented in the root README, run `npm --prefix frontend ci` if needed, then launch `slidekick`. In the dashboard Settings page, choose `default` or `presenter_b` and click **Activate profile**. Start a presentation session and swipe right: `default` advances, whereas `presenter_b` moves back. To switch while presenting: Pause in Session, go to Settings, activate another profile, then Resume.

## Profile API

- `GET /api/profiles` lists validated version-1 profile files and the active profile name.
- `PUT /api/profiles/active` with JSON `{"name":"presenter_b"}` activates a profile. Returns HTTP 409 while a session is running; returns HTTP 400 for an unknown or invalid name.

The `profiles/` folder is read-only to this API. It does not persist the last selected profile after application restart; after restart the default controller bindings apply until a profile is chosen. Invalid JSON and symlinks are excluded from the list.

## Integration boundaries and unfinished work

- A name is used as the local identifier; stable `profile_id`, `gesture_id`, `model_version`, and `revision` fields from the *proposed* integration contract are not implemented yet.
- Switching models, preserving an old model when a new model fails to load, and discarding stale events with a model/profile revision require the finalized R01/R03 event and activation API.
- Frontend and webcam end-to-end behavior require local testing. A saved JSON file should only map gestures the installed recognizer can actually emit.
- The currently supported safe procedure is Pause -> Switch -> Resume. No switching while RUNNING.

## Suggested verification

```bash
python -m pytest -q tests/unit/test_gesture_profile.py tests/unit/test_session_apply_profile.py tests/integration/test_gesture_profile_pipeline.py tests/unit/test_profile_api.py
npm --prefix frontend run build
```

Then demonstrate two valid profiles on a running slideshow. Capture screenshots for the Sprint 5 report only after verifying the real UI.
