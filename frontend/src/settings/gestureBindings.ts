// Gesture-to-command bindings, stored and enforced by the Python API
// (GET/PUT /api/bindings, POST /api/bindings/reset in api_server.py). The
// backend validates every change against command_policy, so "end" can never
// be bound to a gesture.
import { api } from '../core/api'

export type Bindings = Record<string, string>

export interface BindingsInfo {
  bindings: Bindings
  bindableCommands: string[]
  gestures: string[]
}

export type SaveResult = { ok: true; info: BindingsInfo } | { ok: false; error: string }

export const DEFAULT_BINDINGS: Bindings = { swipe_right: 'next', swipe_left: 'previous' }

const GESTURE_LABELS: Record<string, string> = {
  swipe_right: 'Swipe right',
  swipe_left: 'Swipe left',
}

const COMMAND_LABELS: Record<string, string> = {
  next: 'Next slide',
  previous: 'Previous slide',
  pause: 'Pause slideshow',
  resume: 'Resume slideshow',
}

/** "swipe_right" -> "Swipe right"; unknown ids are made readable the same way. */
export function gestureLabel(gesture: string): string {
  if (GESTURE_LABELS[gesture]) return GESTURE_LABELS[gesture]
  const words = gesture.replace(/_/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export function commandLabel(command: string): string {
  return COMMAND_LABELS[command] ?? command
}

type Body = { bindings?: unknown; bindable_commands?: unknown; gestures?: unknown; error?: unknown }

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((v) => typeof v === 'string')
}

function fromBody(body: Body): BindingsInfo | undefined {
  const { bindings, bindable_commands, gestures } = body
  if (typeof bindings !== 'object' || bindings === null) return undefined
  if (!isStringArray(bindable_commands) || !isStringArray(gestures)) return undefined
  return { bindings: bindings as Bindings, bindableCommands: bindable_commands, gestures }
}

const OFFLINE_ERROR = "Can't reach SlideKick, so the bindings weren't saved."

/** The bindings SlideKick is using, or undefined if it can't be reached. */
export async function fetchBindings(): Promise<BindingsInfo | undefined> {
  try {
    const res = await api<Body>('/bindings')
    return res.ok ? fromBody(res.body) : undefined
  } catch {
    return undefined
  }
}

async function send(path: string, method: string, body?: unknown): Promise<SaveResult> {
  try {
    const res = await api<Body>(path, method, body)
    const info = res.ok ? fromBody(res.body) : undefined
    if (info) return { ok: true, info }
    const error = typeof res.body.error === 'string' ? res.body.error : 'The bindings were rejected.'
    return { ok: false, error }
  } catch {
    return { ok: false, error: OFFLINE_ERROR }
  }
}

/** Saves and applies the bindings. The previous bindings stay active if refused. */
export function saveBindings(bindings: Bindings): Promise<SaveResult> {
  return send('/bindings', 'PUT', { bindings })
}

export function resetBindings(): Promise<SaveResult> {
  return send('/bindings/reset', 'POST')
}
