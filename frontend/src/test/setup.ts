import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'
import { fakeBackend, fakeFetch } from './fakeBackend'

beforeEach(() => {
  fakeBackend.reset()
  vi.stubGlobal('fetch', fakeFetch)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})
