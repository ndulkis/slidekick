// Gesture calibration settings shown on the Settings page.
//
// Defaults match the backend GestureCalibration class in
// src/slidekick/recognition/swipe_recognizer.py. Ranges are kept inside what
// that class's validation accepts; confirm them with R03 before release.
//
// These settings are saved in the browser only. The frontend isn't connected
// to the recognition backend yet, so saving them doesn't change how gestures
// are recognized.

export type CalibrationKey = 'swipeDistance' | 'swipeDuration' | 'strictness' | 'cooldown'

export type CalibrationSettings = Record<CalibrationKey, number>

export interface CalibrationControl {
  key: CalibrationKey
  label: string
  description: string
  min: number
  max: number
  step: number
  unit: '%' | 's'
  /** The GestureCalibration field this control maps to. */
  backendField: string
}

export const CALIBRATION_CONTROLS: CalibrationControl[] = [
  {
    key: 'swipeDistance',
    label: 'Swipe distance',
    description: 'How far your hand must move, as a share of the camera width.',
    min: 0.05,
    max: 0.2,
    step: 0.01,
    unit: '%',
    backendField: 'min_displacement',
  },
  {
    key: 'swipeDuration',
    label: 'Slowest allowed swipe',
    description: 'The longest a swipe can take and still count.',
    min: 1.25,
    max: 3,
    step: 0.25,
    unit: 's',
    backendField: 'max_swipe_duration',
  },
  {
    key: 'strictness',
    label: 'Recognition strictness',
    description: 'Higher means fewer accidental gestures but more missed ones.',
    min: 0.4,
    max: 0.8,
    step: 0.05,
    unit: '%',
    backendField: 'confidence_threshold',
  },
  {
    key: 'cooldown',
    label: 'Time between gestures',
    description: 'How long to wait before another gesture is accepted.',
    min: 0.5,
    max: 3,
    step: 0.25,
    unit: 's',
    backendField: 'swipe_cooldown',
  },
]

export const DEFAULT_CALIBRATION: CalibrationSettings = {
  swipeDistance: 0.1,
  swipeDuration: 1.75,
  strictness: 0.55,
  cooldown: 1.5,
}

export const CALIBRATION_STORAGE_KEY = 'slidekick.calibrationProfile'

type CalibrationStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

function browserStorage(): CalibrationStorage | undefined {
  // Accessing localStorage can throw when site data is blocked.
  try {
    return window.localStorage
  } catch {
    return undefined
  }
}

export function isValidCalibration(value: unknown): value is CalibrationSettings {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return CALIBRATION_CONTROLS.every(({ key, min, max }) => {
    const setting = record[key]
    return typeof setting === 'number' && Number.isFinite(setting) && setting >= min && setting <= max
  })
}

/** Returns the saved profile, or the defaults if none is saved or it's invalid. */
export function loadCalibration(storage = browserStorage()): CalibrationSettings {
  try {
    const raw = storage?.getItem(CALIBRATION_STORAGE_KEY)
    if (raw) {
      const parsed: unknown = JSON.parse(raw)
      if (isValidCalibration(parsed)) {
        return {
          swipeDistance: parsed.swipeDistance,
          swipeDuration: parsed.swipeDuration,
          strictness: parsed.strictness,
          cooldown: parsed.cooldown,
        }
      }
    }
  } catch {
    // Unreadable or corrupt data falls through to the defaults.
  }
  return { ...DEFAULT_CALIBRATION }
}

/** Saves the profile. Returns false if it's invalid or couldn't be stored. */
export function saveCalibration(
  settings: CalibrationSettings,
  storage = browserStorage(),
): boolean {
  if (!storage || !isValidCalibration(settings)) return false
  try {
    storage.setItem(CALIBRATION_STORAGE_KEY, JSON.stringify(settings))
    return true
  } catch {
    return false
  }
}

/** Removes the saved profile and returns the defaults. */
export function resetCalibration(storage = browserStorage()): CalibrationSettings {
  try {
    storage?.removeItem(CALIBRATION_STORAGE_KEY)
  } catch {
    // Nothing saved to remove; the defaults apply either way.
  }
  return { ...DEFAULT_CALIBRATION }
}
