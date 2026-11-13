import { api } from '../core/api'

// Gesture calibration settings shown on the Settings page.
//
// Defaults match the backend GestureCalibration class in
// src/slidekick/recognition/swipe_recognizer.py. Ranges are kept inside what
// that class's validation accepts; confirm them with R03 before release.
//
// Settings are loaded from and saved to the running SlideKick app, which
// applies them to recognition right away and keeps them in data/calibration.json.

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
    // Must stay below ideal_displacement (0.20) or the backend rejects it.
    max: 0.19,
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

export function isValidCalibration(value: unknown): value is CalibrationSettings {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return CALIBRATION_CONTROLS.every(({ key, min, max }) => {
    const setting = record[key]
    return typeof setting === 'number' && Number.isFinite(setting) && setting >= min && setting <= max
  })
}

/** Converts to the GestureCalibration field names the API uses. */
export function toBackend(settings: CalibrationSettings): Record<string, number> {
  return Object.fromEntries(
    CALIBRATION_CONTROLS.map(({ key, backendField }) => [backendField, settings[key]]),
  )
}

/** Converts from the API's field names; undefined if any value is missing or out of range. */
export function fromBackend(body: unknown): CalibrationSettings | undefined {
  if (typeof body !== 'object' || body === null) return undefined
  const record = body as Record<string, unknown>
  const settings = Object.fromEntries(
    CALIBRATION_CONTROLS.map(({ key, backendField }) => [key, record[backendField]]),
  )
  return isValidCalibration(settings) ? settings : undefined
}

/** The calibration SlideKick is using, or undefined if it can't be reached. */
export async function fetchCalibration(): Promise<CalibrationSettings | undefined> {
  try {
    const res = await api<unknown>('/calibration')
    return res.ok ? fromBackend(res.body) : undefined
  } catch {
    return undefined
  }
}

/** Applies and saves the calibration. Returns false if it was refused or SlideKick can't be reached. */
export async function saveCalibration(settings: CalibrationSettings): Promise<boolean> {
  if (!isValidCalibration(settings)) return false
  try {
    return (await api('/calibration', 'PUT', toBackend(settings))).ok
  } catch {
    return false
  }
}
