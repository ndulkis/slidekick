import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import CameraPreview from './CameraPreview'

describe('CameraPreview', () => {
  it('shows no camera source message when hasCamera is false', () => {
    render(<CameraPreview status="ready" hasCamera={false} />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('No camera source is available.')
    expect(status).toHaveClass('camera-preview', 'camera-preview-empty')
  })

  it('shows loading message when status is loading', () => {
    render(<CameraPreview status="loading" hasCamera={true} />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Starting camera...')
    expect(status).toHaveClass('camera-preview', 'camera-preview-loading')
  })

  it('shows an alert when status is error', () => {
    render(<CameraPreview status="error" hasCamera={true} />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent(
      'Camera not available. Check camera access and try again.',
    )
    expect(alert).toHaveClass('camera-preview', 'camera-preview-error')
  })

  it('shows the preview when ready', () => {
    render(<CameraPreview status="ready" hasCamera={true} />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Camera preview')
    expect(status).toHaveClass('camera-preview', 'camera-preview-ready')
  })

  it('shows the preview when active', () => {
    render(<CameraPreview status="active" hasCamera={true} />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Camera preview')
    expect(status).toHaveClass('camera-preview', 'camera-preview-active')
  })

  it('shows the paused label when paused', () => {
    render(<CameraPreview status="paused" hasCamera={true} />)
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Camera preview (paused)')
    expect(status).toHaveClass('camera-preview', 'camera-preview-paused')
  })

  it('prioritizes hasCamera=false over an error status', () => {
    render(<CameraPreview status="error" hasCamera={false} />)

    expect(screen.getByRole('status')).toHaveTextContent(
      'No camera source is available.',
    )
    expect(
      screen.queryByText('Camera not available. Check camera access and try again.'),
    ).not.toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
