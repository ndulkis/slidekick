import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import OverlaySection from './OverlaySection'

const toggle = () => screen.getByRole('checkbox', { name: 'Show the overlay during presentations' })
const corner = (name: string) => screen.getByRole('radio', { name })

describe('OverlaySection', () => {
  it('loads the saved settings', async () => {
    fakeBackend.overlay = { enabled: true, position: 'bottom-left' }
    render(<OverlaySection />)
    await waitFor(() => expect(corner('Bottom left')).toBeChecked())
    expect(toggle()).toBeChecked()
  })

  it('saves a new position right away', async () => {
    render(<OverlaySection />)
    await waitFor(() => expect(corner('Top right')).toBeChecked())

    fireEvent.click(corner('Bottom right'))

    await waitFor(() =>
      expect(fakeBackend.overlay).toEqual({ enabled: true, position: 'bottom-right' }),
    )
    expect(corner('Bottom right')).toBeChecked()
  })

  it('turns the overlay off and disables the positions', async () => {
    render(<OverlaySection />)
    await waitFor(() => expect(toggle()).toBeChecked())

    fireEvent.click(toggle())

    await waitFor(() => expect(fakeBackend.overlay.enabled).toBe(false))
    expect(toggle()).not.toBeChecked()
    expect(corner('Top left')).toBeDisabled()
  })

  it('keeps the old setting and says so when saving fails', async () => {
    render(<OverlaySection />)
    await waitFor(() => expect(corner('Top right')).toBeChecked())

    fakeBackend.online = false
    fireEvent.click(corner('Top left'))

    expect(await screen.findByRole('alert')).toHaveTextContent("Couldn't save")
    expect(corner('Top right')).toBeChecked()
  })
})
