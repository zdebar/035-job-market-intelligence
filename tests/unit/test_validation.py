from decimal import Decimal
from pathlib import Path

import pytest

from job_market_intelligence.processing.validation import HoursValidationRules

PROJECT_ROOT = Path(__file__).parents[2]


def test_hours_validation_accepts_configured_weekly_range() -> None:
    rules = HoursValidationRules.from_project_root(PROJECT_ROOT)

    rules.validate(Decimal("20"), Decimal("30"), "week")


def test_hours_validation_rejects_range_above_period_limit() -> None:
    rules = HoursValidationRules.from_project_root(PROJECT_ROOT)

    with pytest.raises(ValueError, match="week limit"):
        rules.validate(Decimal("20"), Decimal("169"), "week")
