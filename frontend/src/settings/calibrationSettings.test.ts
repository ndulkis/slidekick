import { describe, expect, it } from 'vitest'
import {
  CALIBRATION_CONTROLS,
  CALIBRATION_STORAGE_KEY,
  DEFAULT_CALIBRATION,
  loadCalibration,
  resetCalibration,
  saveCalibration,
} from './calibrationSettings'

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial))
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value)
    },
    removeItem: (key: string) => {
      data.delete(key)
    },
  }
}

function failingStorage() {
  return {
    getItem: () => {
      throw new Error('blocked')
    },
    setItem: () => {
      throw new Error('quota exceeded')
    },
    removeItem: () => {
      throw new Error('blocked')
    },
  }
}

describe('calibrationSettings', () => {
  it('uses the backend GestureCalibration defaults', () => {
    // Values from src/slidekick/recognition/swipe_recognizer.py.
    expect(DEFAULT_CALIBRATION).toEqual({
      swipeDistance: 0.1,
      swipeDuration: 1.75,
      strictness: 0.55,
      cooldown: 1.5,
    })
  })

  it('keeps every default inside its control range', () => {
    for (const { key, min, max } of CALIBRATION_CONTROLS) {
      expect(DEFAULT_CALIBRATION[key]).toBeGreaterThanOrEqual(min)
      expect(DEFAULT_CALIBRATION[key]).toBeLessThanOrEqual(max)
    }
  })

  it('returns the defaults when nothing is saved', () => {
    expect(loadCalibration(memoryStorage())).toEqual(DEFAULT_CALIBRATION)
  })

  it('loads a saved profile', () => {
    const storage = memoryStorage()
    const profile = { swipeDistance: 0.15, swipeDuration: 2.5, strictness: 0.7, cooldown: 1 }

    expect(saveCalibration(profile, storage)).toBe(true)
    expect(loadCalibration(storage)).toEqual(profile)
  })

  it('falls back to the defaults for corrupt data', () => {
    const storage = memoryStorage({ [CALIBRATION_STORAGE_KEY]: 'not json' })
    expect(loadCalibration(storage)).toEqual(DEFAULT_CALIBRATION)
  })

  it('falls back to the defaults for out-of-range values', () => {
    const storage = memoryStorage({
      [CALIBRATION_STORAGE_KEY]: JSON.stringify({ ...DEFAULT_CALIBRATION, strictness: 2 }),
    })
    expect(loadCalibration(storage)).toEqual(DEFAULT_CALIBRATION)
  })

  it('refuses to save an invalid profile', () => {
    const storage = memoryStorage()
    expect(saveCalibration({ ...DEFAULT_CALIBRATION, cooldown: -1 }, storage)).toBe(false)
    expect(storage.getItem(CALIBRATION_STORAGE_KEY)).toBeNull()
  })

  it('reports a failed save and still loads the defaults', () => {
    const storage = failingStorage()
    expect(saveCalibration(DEFAULT_CALIBRATION, storage)).toBe(false)
    expect(loadCalibration(storage)).toEqual(DEFAULT_CALIBRATION)
  })

  it('reset removes the saved profile and returns the defaults', () => {
    const storage = memoryStorage()
    saveCalibration({ ...DEFAULT_CALIBRATION, cooldown: 3 }, storage)

    expect(resetCalibration(storage)).toEqual(DEFAULT_CALIBRATION)
    expect(storage.getItem(CALIBRATION_STORAGE_KEY)).toBeNull()
  })
})
