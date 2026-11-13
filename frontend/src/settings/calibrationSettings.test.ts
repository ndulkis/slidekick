import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import {
  CALIBRATION_CONTROLS,
  DEFAULT_CALIBRATION,
  fetchCalibration,
  fromBackend,
  saveCalibration,
  toBackend,
} from './calibrationSettings'

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

  it('converts to and from the backend field names', () => {
    const backend = toBackend(DEFAULT_CALIBRATION)
    expect(backend).toEqual({
      min_displacement: 0.1,
      max_swipe_duration: 1.75,
      confidence_threshold: 0.55,
      swipe_cooldown: 1.5,
    })
    expect(fromBackend(backend)).toEqual(DEFAULT_CALIBRATION)
  })

  it('rejects backend values that are missing or out of range', () => {
    expect(fromBackend({ ...toBackend(DEFAULT_CALIBRATION), swipe_cooldown: 99 })).toBeUndefined()
    expect(fromBackend({ min_displacement: 0.1 })).toBeUndefined()
    expect(fromBackend(null)).toBeUndefined()
  })

  it('loads and saves through the API', async () => {
    const profile = { swipeDistance: 0.15, swipeDuration: 2.5, strictness: 0.7, cooldown: 1 }

    expect(await saveCalibration(profile)).toBe(true)
    expect(await fetchCalibration()).toEqual(profile)
  })

  it('refuses to send an invalid profile', async () => {
    expect(await saveCalibration({ ...DEFAULT_CALIBRATION, cooldown: -1 })).toBe(false)
    expect(fakeBackend.calibration.swipe_cooldown).toBe(DEFAULT_CALIBRATION.cooldown)
  })

  it('reports failure when SlideKick refuses or is unreachable', async () => {
    fakeBackend.rejectCalibration = true
    expect(await saveCalibration(DEFAULT_CALIBRATION)).toBe(false)

    fakeBackend.online = false
    expect(await saveCalibration(DEFAULT_CALIBRATION)).toBe(false)
    expect(await fetchCalibration()).toBeUndefined()
  })
})
