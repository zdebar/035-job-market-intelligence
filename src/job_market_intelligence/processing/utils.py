"""Utilities shared by raw-data parsers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def parse_datetime(value: Any) -> datetime | None:
    """Parse an ISO timestamp and make date-only values UTC timestamps."""
    text = optional_text(value)
    if not text:
        return None
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def optional_text(value: Any) -> str | None:
    """Return a stripped string or None for an empty value."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
