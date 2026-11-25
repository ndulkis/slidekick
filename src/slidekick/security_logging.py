"""Centralized structured logging for SlideKick security events."""

import json
import logging
from datetime import UTC, datetime

logger = logging.getLogger("slidekick.security")

VALID_SEVERITIES = {
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def log_security_event(
    event_type: str,
    component: str,
    severity: str,
    outcome: str,
) -> None:
    """Emit a structured security event using trusted metadata."""

    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Unsupported security severity: {severity!r}")

    event = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "component": component,
        "severity": severity,
        "outcome": outcome,
    }

    logger.log(
        VALID_SEVERITIES[severity],
        json.dumps(event),
    )
