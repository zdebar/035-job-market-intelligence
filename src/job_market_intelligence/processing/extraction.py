"""Shared extraction helpers for normalized job data."""

from __future__ import annotations

import re
from decimal import Decimal

HOURS_PATTERN = re.compile(
    r"(?P<minimum>\d{1,3})\s*"
    r"(?:(?:[-\u2013\u2014]|\bto\b|\ba\u017e\b)\s*(?P<maximum>\d{1,3}))?\s*"
    r"(?:hours?|hodin|h)\b"
    r"(?:\s*(?:per|/|a|za)\s*)?"
    r"\s*(?P<period>week|weekly|t\u00fdden|t\u00fddn\u011b|month|monthly|"
    r"m\u011bs\u00edc|m\u011bs\u00ed\u010dn\u011b|day|daily|denn\u011b|"
    r"year|annually|rok|ro\u010dn\u011b)?",
    flags=re.IGNORECASE,
)


def extract_hours(text: str) -> tuple[Decimal | None, Decimal | None, str | None]:
    """Extract the first explicit workload range from text."""
    match = HOURS_PATTERN.search(text)
    if not match:
        return None, None, None

    minimum = Decimal(match.group("minimum"))
    maximum_text = match.group("maximum")
    maximum = Decimal(maximum_text) if maximum_text else minimum
    period = normalize_hours_period(match.group("period"))
    return minimum, maximum, period


def normalize_hours_period(value: str | None) -> str | None:
    """Map source workload units to database values."""
    if not value:
        return None
    normalized = value.casefold()
    if normalized in {"week", "weekly", "\u00fdden", "t\u00fddn\u011b"}:
        return "week"
    if normalized in {"month", "monthly", "m\u011bs\u00edc", "m\u011bs\u00ed\u010dn\u011b"}:
        return "month"
    if normalized in {"day", "daily", "denn\u011b"}:
        return "day"
    if normalized in {"year", "annually", "rok", "ro\u010dn\u011b"}:
        return "year"
    return None
