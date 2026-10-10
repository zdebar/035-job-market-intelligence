"""Shared parsing and normalization helpers for source adapters."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from job_market_intelligence.processing.extraction import extract_hours
from job_market_intelligence.processing.models import (
    EmploymentOption,
    SkillRequirement,
)
from job_market_intelligence.processing.normalization import NormalizationDictionaries
from job_market_intelligence.processing.validation import HoursValidationRules


class ParserSupport:
    """Apply project-wide deterministic extraction rules."""

    def __init__(self, project_root: Path) -> None:
        self.normalizer = NormalizationDictionaries.from_project_root(project_root)
        self.hours_validation = HoursValidationRules.from_project_root(project_root)

    def company_name(self, value: Any, default: str) -> str:
        text = str(value or default).strip()
        canonical = self.normalizer.companies.find_first(text)
        if canonical:
            return canonical
        if text:
            return text
        raise ValueError("Job has no company")

    def locations(self, values: Iterable[Any]) -> tuple[str, ...]:
        names: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text:
                names.extend(self.normalizer.locations.find_non_overlapping(text))
        return tuple(dict.fromkeys(names))

    def work_modes(self, metadata_text: str, search_text: str) -> tuple[str, ...]:
        matches = self.normalizer.work_modes.find_all(metadata_text)
        return matches or self.normalizer.work_modes.find_all(search_text)

    def employment_options(
        self,
        metadata_text: str,
        search_text: str,
    ) -> tuple[EmploymentOption, ...]:
        relation_name = self.normalizer.employment_relations.find_first(metadata_text)
        workload_name = self.normalizer.workloads.find_first(f"{metadata_text}\n{search_text}")
        hours_min, hours_max, hours_period = extract_hours(search_text)
        self.hours_validation.validate(hours_min, hours_max, hours_period)
        options: list[EmploymentOption] = []
        if not any((relation_name, workload_name, hours_min, hours_max, hours_period)):
            return tuple(options)
        options.append(
            EmploymentOption(
                employment_relation_name=relation_name,
                workload_name=workload_name,
                hours_min=hours_min,
                hours_max=hours_max,
                hours_period=hours_period,
            )
        )
        return tuple(options)

    def skills(self, search_text: str) -> tuple[SkillRequirement, ...]:
        return tuple(
            SkillRequirement(name=skill_name)
            for skill_name in self.normalizer.skills.find_all(search_text)
        )


def text_value(value: Any) -> str:
    """Convert a scalar source value to searchable text."""
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(text_value(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(text_value(item) for item in value)
    return str(value)


def salary_period(value: Any) -> str | None:
    """Map source salary intervals to database values."""
    text = text_value(value).casefold()
    for period in ("hour", "day", "week", "month", "year", "project"):
        if period in text:
            return period
    if "annual" in text:
        return "year"
    return None


def decimal_value(value: Any) -> Decimal | None:
    """Convert a source numeric value to Decimal."""
    if value is None or value == "":
        return None
    return Decimal(str(value))
