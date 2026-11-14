// In-memory stand-in for the Python API (src/slidekick/api_server.py), installed
// as global fetch for every test in setup.ts. Transitions mirror
// SessionController; the real ones are tested in tests/unit/test_session_controller.py.
import type { SessionState } from '../core/sessionContracts'
import type { CameraStatus } from '../core/useSession'
import type { Gesture } from '../session/types'
import { DEFAULT_CALIBRATION, toBackend } from '../settings/calibrationSettings'

const TRANSITIONS = {
  start: { from: ['idle', 'ended'], to: 'running', type: 'session_started', use_case: 'UC10' },
  pause: { from: ['running'], to: 'paused', type: 'session_paused', use_case: 'UC6' },
  resume: { from: ['paused'], to: 'running', type: 'session_resumed', use_case: 'UC7' },
  end: { from: ['running'], to: 'ended', type: 'session_ended', use_case: 'UC8' },
} as const

function initial() {
  return {
    online: true,
    state: 'idle' as SessionState,
    camera: 'off' as CameraStatus,
    /** What the camera becomes when a session starts. */
    cameraOnStart: 'ready' as CameraStatus,
    lastGesture: null as { id: number; gesture: Gesture; confidence: number | null } | null,
    presentationError: null as string | null,
    calibration: toBackend(DEFAULT_CALIBRATION) as Record<string, number>,
    /** When set, PUT /api/calibration answers 400. */
    rejectCalibration: false,
    /** Set by POST /api/quit. */
    hasQuit: false,
    gestureId: 0,
  }
}

export const fakeBackend = {
  ...initial(),
  reset() {
    Object.assign(fakeBackend, initial())
  },
  /** A recognized gesture that ran a command, as the camera loop reports it. */
  emitGesture(gesture: Gesture, confidence: number | null = null) {
    fakeBackend.gestureId += 1
    fakeBackend.lastGesture = { id: fakeBackend.gestureId, gesture, confidence }
  },
}

function status() {
  return {
    state: fakeBackend.state,
    camera: fakeBackend.camera,
    last_gesture: fakeBackend.lastGesture,
    presentation_error: fakeBackend.presentationError,
  }
}

function json(body: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

export function fakeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  if (!fakeBackend.online) return Promise.reject(new TypeError('Failed to fetch'))
  const path = String(input)
  const method = init?.method ?? 'GET'

  if (path === '/api/session' && method === 'GET') return json(status())

  const action = path.match(/^\/api\/session\/(\w+)$/)?.[1]
  if (action && method === 'POST') {
    const t = TRANSITIONS[action as keyof typeof TRANSITIONS]
    if (!t) return json({ error: 'Unknown action' }, 404)
    if (!(t.from as readonly SessionState[]).includes(fakeBackend.state)) {
      return json({ error: `Cannot ${action}`, ...status() }, 409)
    }
    const previous = fakeBackend.state
    fakeBackend.state = t.to
    fakeBackend.lastGesture = null
    if (action === 'start') fakeBackend.camera = fakeBackend.cameraOnStart
    if (action === 'end') fakeBackend.camera = 'off'
    return json({
      event: { type: t.type, previous_state: previous, new_state: t.to, use_case: t.use_case },
      ...status(),
    })
  }

  if (path === '/api/quit' && method === 'POST') {
    fakeBackend.hasQuit = true
    return json({ quitting: true })
  }

  if (path === '/api/calibration') {
    if (method === 'GET') return json(fakeBackend.calibration)
    if (method === 'PUT') {
      if (fakeBackend.rejectCalibration) return json({ error: 'Invalid calibration' }, 400)
      fakeBackend.calibration = JSON.parse(String(init?.body))
      return json(fakeBackend.calibration)
    }
  }

  return json({ error: 'Not found' }, 404)
}
