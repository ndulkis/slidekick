import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import StartEndControl from './StartEndControl'

describe('StartEndControl', () => {
  it('enables Start and disables End when ready', () => {
    render(<StartEndControl status="ready" onStart={vi.fn()} onEnd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start session' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'End session' })).toBeDisabled()
  })

  it('disables Start and enables End when active', () => {
    render(<StartEndControl status="active" onStart={vi.fn()} onEnd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start session' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'End session' })).toBeEnabled()
  })

  it('disables both Start and End when paused', () => {
    render(<StartEndControl status="paused" onStart={vi.fn()} onEnd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start session' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'End session' })).toBeDisabled()
  })

  it('offers Start new session and disables End when ended', () => {
    render(<StartEndControl status="ended" onStart={vi.fn()} onEnd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start new session' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'End session' })).toBeDisabled()
  })

  it('disables both Start and End when loading', () => {
    render(<StartEndControl status="loading" onStart={vi.fn()} onEnd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start session' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'End session' })).toBeDisabled()
  })

  it('disables both Start and End when in error', () => {
    render(<StartEndControl status="error" onStart={vi.fn()} onEnd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start session' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'End session' })).toBeDisabled()
  })

  it('calls onStart when Start is clicked', () => {
    const onStart = vi.fn()
    const onEnd = vi.fn()
    render(<StartEndControl status="ready" onStart={onStart} onEnd={onEnd} />)

    fireEvent.click(screen.getByRole('button', { name: 'Start session' }))

    expect(onStart).toHaveBeenCalledTimes(1)
    expect(onEnd).not.toHaveBeenCalled()
  })

  it('calls onEnd when End is clicked', () => {
    const onStart = vi.fn()
    const onEnd = vi.fn()
    render(<StartEndControl status="active" onStart={onStart} onEnd={onEnd} />)

    fireEvent.click(screen.getByRole('button', { name: 'End session' }))

    expect(onEnd).toHaveBeenCalledTimes(1)
    expect(onStart).not.toHaveBeenCalled()
  })
})
