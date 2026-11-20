import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import DashboardPage from './DashboardPage'

function renderDashboard() {
  render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

function item(label: string) {
  const row = screen.getByText(label, { selector: '.dashboard-check-label' }).closest('li')
  if (!row) throw new Error(`No checklist row for ${label}`)
  return within(row)
}

describe('DashboardPage', () => {
  it('says ready to present when everything checks out', async () => {
    renderDashboard()
    expect(await screen.findByText('Ready to present')).toBeInTheDocument()
    expect(item('SlideKick').getByText('Running')).toBeInTheDocument()
    expect(item('Camera').getByText('MacBook Pro Camera')).toBeInTheDocument()
    expect(item('Session').getByText('Not started')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Go to Session' })).toHaveAttribute('href', '/session')
  })

  it('says how to start SlideKick when it cannot be reached', async () => {
    fakeBackend.online = false
    renderDashboard()
    expect(await screen.findByText('Something needs attention')).toBeInTheDocument()
    expect(item('SlideKick').getByText(/Start it with slidekick/)).toBeInTheDocument()
  })

  it('flags a missing camera', async () => {
    fakeBackend.cameras = []
    renderDashboard()
    expect(await screen.findByText('No camera found. Connect one.')).toBeInTheDocument()
    expect(screen.getByText('Something needs attention')).toBeInTheDocument()
  })

  it('flags a failed slide command', async () => {
    fakeBackend.presentationError = 'Presentation command failed: no slideshow'
    renderDashboard()
    expect(
      await screen.findByText('Presentation command failed: no slideshow'),
    ).toBeInTheDocument()
  })

  it('links back to a running session', async () => {
    fakeBackend.state = 'running'
    fakeBackend.camera = 'ready'
    renderDashboard()
    expect(await screen.findByRole('link', { name: 'Back to the session' })).toBeInTheDocument()
    expect(item('Session').getByText('Running')).toBeInTheDocument()
  })
})
