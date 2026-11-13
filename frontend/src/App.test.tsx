import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'
import { fakeBackend } from './test/fakeBackend'

describe('App routing', () => {
  it('renders the dashboard at the root route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole('heading', { name: 'Dashboard' }),
    ).toBeInTheDocument()
  })

  it('renders the session view at /session', () => {
    render(
      <MemoryRouter initialEntries={['/session']}>
        <App />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole('heading', { name: 'Presentation Session' }),
    ).toBeInTheDocument()
  })

  it('renders the settings view at /settings', () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <App />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole('heading', { name: 'Settings' }),
    ).toBeInTheDocument()
  })

  it('shows the gesture calibration section on the settings view', () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <App />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole('heading', { name: 'Gesture Calibration' }),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('slider')).toHaveLength(4)
  })

  it('quits SlideKick from any page and replaces the app with a quit screen', async () => {
    render(
      <MemoryRouter initialEntries={['/settings']}>
        <App />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Quit SlideKick' }))

    expect(await screen.findByRole('heading', { name: 'SlideKick has quit' })).toBeInTheDocument()
    expect(fakeBackend.hasQuit).toBe(true)
    expect(screen.queryByRole('link', { name: 'Session' })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Settings' })).not.toBeInTheDocument()
  })

  it('shows the quit screen even when SlideKick is already gone', async () => {
    fakeBackend.online = false
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Quit SlideKick' }))

    expect(await screen.findByRole('heading', { name: 'SlideKick has quit' })).toBeInTheDocument()
  })
})
