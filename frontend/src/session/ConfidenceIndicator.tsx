interface ConfidenceIndicatorProps {
  confidence?: number
}

function ConfidenceIndicator({ confidence }: ConfidenceIndicatorProps) {
  if (confidence === undefined) {
    return (
      <span className="confidence-indicator confidence-unavailable">
        Confidence unavailable
      </span>
    )
  }

  const percent = Math.round(confidence * 100)

  return (
    <span className="confidence-indicator" aria-label={`Confidence ${percent}%`}>
      {percent}% confidence
    </span>
  )
}

export default ConfidenceIndicator
