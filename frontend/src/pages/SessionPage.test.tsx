import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SessionPage from './SessionPage'

function sessionStatusButton(name: string) {
  return within(screen.getByRole('group', { name: 'Session status' })).getByRole('button', {
    name,
  })
}

describe('SessionPage', () => {
  it('renders the default Ready state', () => {
    render(<SessionPage />)
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('Presentation: Connected')).toBeInTheDocument()
  })

  it('shows camera unavailable message when camera is missing', () => {
    render(<SessionPage />)
    fireEvent.click(screen.getByRole('button', { name: 'camera unavailable' }))
    expect(screen.getByText('No camera source is available.')).toBeInTheDocument()
  })

  it('switches to Active and shows Pause control', () => {
    render(<SessionPage />)
    fireEvent.click(sessionStatusButton('active'))
    expect(screen.getByRole('button', { name: 'Pause session' })).toBeEnabled()
  })

  it('shows gesture feedback with confidence when a gesture is selected', () => {
    render(<SessionPage />)
    fireEvent.click(sessionStatusButton('active'))
    fireEvent.click(screen.getByRole('button', { name: 'next' }))
    expect(screen.getAllByText('Next').length).toBeGreaterThan(0)
    expect(screen.getByText('92% confidence')).toBeInTheDocument()
  })

  it('treats no-gesture as a normal state, not an error', () => {
    render(<SessionPage />)
    fireEvent.click(sessionStatusButton('active'))
    fireEvent.click(screen.getByRole('button', { name: 'none' }))
    expect(screen.getByText('No gesture detected')).toBeInTheDocument()
  })

  it('shows the error message when session status is error', () => {
    render(<SessionPage />)
    fireEvent.click(sessionStatusButton('error'))
    expect(
      screen.getByText(
        'Something required by this session is unavailable. Check camera access and try again.',
      ),
    ).toBeInTheDocument()
  })
})
