import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SessionStatusBadge from './SessionStatusBadge'

describe('SessionStatusBadge', () => {
  it('renders the loading state', () => {
    render(<SessionStatusBadge status="loading" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Session starting')
    expect(status).toHaveClass('status-badge', 'status-badge-loading')
  })

  it('renders the ready state', () => {
    render(<SessionStatusBadge status="ready" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Ready')
    expect(status).toHaveClass('status-badge', 'status-badge-ready')
  })

  it('renders the active state', () => {
    render(<SessionStatusBadge status="active" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Active')
    expect(status).toHaveClass('status-badge', 'status-badge-active')
  })

  it('renders the paused state', () => {
    render(<SessionStatusBadge status="paused" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Paused')
    expect(status).toHaveClass('status-badge', 'status-badge-paused')
  })

  it('renders the error state', () => {
    render(<SessionStatusBadge status="error" />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Error')
    expect(status).toHaveClass('status-badge', 'status-badge-error')
  })
})
