"""Configurable validation rules for normalized job data."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from job_market_intelligence.ingestion.config import load_toml

DEFAULT_CONFIG_PATH = Path("config/validation.toml")


@dataclass(frozen=True)
class HoursValidationRules:
    """Validate workload hours against configured physical limits."""

    minimum: Decimal
    maximum: Decimal
    maximum_by_period: dict[str, Decimal]

    @classmethod
    def from_project_root(cls, project_root: Path) -> HoursValidationRules:
        """Load hour limits from the project configuration."""
        return cls.from_config(project_root / DEFAULT_CONFIG_PATH)

    @classmethod
    def from_config(cls, config_path: Path) -> HoursValidationRules:
        """Create rules from a TOML configuration file."""
        config = load_toml(config_path)
        hours = _mapping(config, "hours")
        period_limits = _mapping(hours, "maximum_by_period")
        return cls(
            minimum=_decimal(hours, "minimum"),
            maximum=_decimal(hours, "maximum"),
            maximum_by_period={
                period: Decimal(str(limit)) for period, limit in period_limits.items()
            },
        )

    def validate(
        self,
        minimum: Decimal | None,
        maximum: Decimal | None,
        period: str | None,
    ) -> None:
        """Raise ValueError when an extracted hour range is invalid."""
        if minimum is None and maximum is None:
            return
        if minimum is not None and minimum < self.minimum:
            raise ValueError(f"Hours minimum is below the configured limit: {minimum}")
        if maximum is not None and maximum < self.minimum:
            raise ValueError(f"Hours maximum is below the configured limit: {maximum}")
        if minimum is not None and maximum is not None and maximum < minimum:
            raise ValueError(f"Hours maximum is below minimum: {maximum} < {minimum}")

        period_maximum = (
            self.maximum if period is None else self.maximum_by_period.get(period, self.maximum)
        )
        if minimum is not None and minimum > period_maximum:
            raise ValueError(
                f"Hours minimum exceeds the configured {period or 'general'} limit: "
                f"{minimum} > {period_maximum}"
            )
        if maximum is not None and maximum > period_maximum:
            raise ValueError(
                f"Hours maximum exceeds the configured {period or 'general'} limit: "
                f"{maximum} > {period_maximum}"
            )


def _mapping(value: dict[str, Any], key: str) -> dict[str, Any]:
    nested = value.get(key)
    if not isinstance(nested, dict):
        raise ValueError(f"Validation configuration section is missing: {key}")
    return nested


def _decimal(value: dict[str, Any], key: str) -> Decimal:
    setting = value.get(key)
    if setting is None:
        raise ValueError(f"Validation configuration value is missing: {key}")
    return Decimal(str(setting))
