import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import PauseResumeControl from './PauseResumeControl'

describe('PauseResumeControl', () => {
  it('renders disabled Pause button when loading', () => {
    render(<PauseResumeControl status="loading" onPause={vi.fn()} onResume={vi.fn()} />)
    const button = screen.getByRole('button', { name: 'Pause session' })
    expect(button).toHaveTextContent('Pause')
    expect(button).toBeDisabled()
  })

  it('renders disabled Pause button when ready', () => {
    render(<PauseResumeControl status="ready" onPause={vi.fn()} onResume={vi.fn()} />)
    const button = screen.getByRole('button', { name: 'Pause session' })
    expect(button).toHaveTextContent('Pause')
    expect(button).toBeDisabled()
  })

  it('renders enabled Pause button when active', () => {
    render(<PauseResumeControl status="active" onPause={vi.fn()} onResume={vi.fn()} />)
    const button = screen.getByRole('button', { name: 'Pause session' })
    expect(button).toHaveTextContent('Pause')
    expect(button).toBeEnabled()
  })

  it('renders enabled Resume button when paused', () => {
    render(<PauseResumeControl status="paused" onPause={vi.fn()} onResume={vi.fn()} />)
    const button = screen.getByRole('button', { name: 'Resume session' })
    expect(button).toHaveTextContent('Resume')
    expect(button).toBeEnabled()
  })

  it('renders disabled Pause button when in error', () => {
    render(<PauseResumeControl status="error" onPause={vi.fn()} onResume={vi.fn()} />)
    const button = screen.getByRole('button', { name: 'Pause session' })
    expect(button).toHaveTextContent('Pause')
    expect(button).toBeDisabled()
  })

  it('calls onPause when clicked while active', () => {
    const onPause = vi.fn()
    const onResume = vi.fn()
    render(<PauseResumeControl status="active" onPause={onPause} onResume={onResume} />)

    fireEvent.click(screen.getByRole('button', { name: 'Pause session' }))

    expect(onPause).toHaveBeenCalledTimes(1)
    expect(onResume).not.toHaveBeenCalled()
  })

  it('calls onResume when clicked while paused', () => {
    const onPause = vi.fn()
    const onResume = vi.fn()
    render(<PauseResumeControl status="paused" onPause={onPause} onResume={onResume} />)

    fireEvent.click(screen.getByRole('button', { name: 'Resume session' }))

    expect(onResume).toHaveBeenCalledTimes(1)
    expect(onPause).not.toHaveBeenCalled()
  })
})
