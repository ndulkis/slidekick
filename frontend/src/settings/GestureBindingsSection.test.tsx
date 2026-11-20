import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { fakeBackend } from '../test/fakeBackend'
import GestureBindingsSection from './GestureBindingsSection'

function select(name: string) {
  return screen.getByLabelText(name) as HTMLSelectElement
}

function click(name: string) {
  fireEvent.click(screen.getByRole('button', { name }))
}

async function renderLoaded() {
  render(<GestureBindingsSection />)
  await waitFor(() => expect(select('Swipe right')).toBeEnabled())
}

describe('GestureBindingsSection', () => {
  it('loads the bindings SlideKick is using', async () => {
    fakeBackend.bindings = { swipe_right: 'pause', swipe_left: 'previous' }
    await renderLoaded()

    expect(screen.getByRole('heading', { name: 'Gesture Bindings' })).toBeInTheDocument()
    expect(select('Swipe right').value).toBe('pause')
    expect(select('Swipe left').value).toBe('previous')
  })

  it('never offers ending the session as a gesture', async () => {
    await renderLoaded()

    const options = Array.from(select('Swipe right').options).map((o) => o.value)
    expect(options).toEqual(['next', 'pause', 'previous', 'resume'])
  })

  it('saves a change to SlideKick and announces it', async () => {
    await renderLoaded()

    fireEvent.change(select('Swipe right'), { target: { value: 'previous' } })
    click('Save bindings')

    expect(await screen.findByText('Gesture bindings saved.')).toBeInTheDocument()
    expect(fakeBackend.bindings.swipe_right).toBe('previous')
  })

  it('resets SlideKick to the defaults and announces it', async () => {
    fakeBackend.bindings = { swipe_right: 'previous', swipe_left: 'next' }
    await renderLoaded()

    click('Reset bindings to defaults')

    expect(await screen.findByText('Gesture bindings reset to defaults.')).toBeInTheDocument()
    expect(select('Swipe right').value).toBe('next')
    expect(fakeBackend.bindings).toEqual({ swipe_right: 'next', swipe_left: 'previous' })
  })

  it('shows the reason when SlideKick refuses the bindings', async () => {
    await renderLoaded()
    // Force a choice the backend refuses (the page never offers "end" itself).
    const draft = select('Swipe left')
    const bad = document.createElement('option')
    bad.value = 'end'
    draft.appendChild(bad)
    fireEvent.change(draft, { target: { value: 'end' } })
    click('Save bindings')

    expect(await screen.findByRole('alert')).toHaveTextContent(/not a bindable command/)
    expect(fakeBackend.bindings.swipe_left).toBe('previous')
  })

  it('says so and disables changes when SlideKick is not running', async () => {
    fakeBackend.online = false
    render(<GestureBindingsSection />)

    expect(await screen.findByText(/SlideKick isn't running/)).toBeInTheDocument()
    expect(select('Swipe right')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Save bindings' })).toBeDisabled()
  })

  it('can be changed and saved with the keyboard alone', async () => {
    const user = userEvent.setup()
    await renderLoaded()

    select('Swipe right').focus()
    await user.selectOptions(select('Swipe right'), 'pause')
    await user.tab() // Swipe right is listed after Swipe left, so Save is next
    expect(screen.getByRole('button', { name: 'Save bindings' })).toHaveFocus()
    await user.keyboard('{Enter}')

    expect(await screen.findByText('Gesture bindings saved.')).toBeInTheDocument()
    expect(fakeBackend.bindings.swipe_right).toBe('pause')
  })
})
