import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

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
})
