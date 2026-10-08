"""Models shared by raw-data parsers and database writers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SkillRequirement:
    """A normalized skill found in a job advertisement."""

    name: str
    proficiency_level_name: str | None = None
    requirement_type_name: str | None = None
    priority: int | None = None


@dataclass(frozen=True)
class EmploymentOption:
    """One legal employment relation and workload combination."""

    employment_relation_name: str | None = None
    workload_name: str | None = None
    hours_min: Decimal | None = None
    hours_max: Decimal | None = None
    hours_period: str | None = None


@dataclass(frozen=True)
class ParsedJobPosting:
    """Normalized data extracted from one source advertisement."""

    source_job_id: str
    company_name: str
    role_name: str | None
    seniority_level_name: str | None
    source_url: str | None
    source_published_at: datetime | None
    source_updated_at: datetime | None
    raw_advertisement: dict[str, Any]
    locations: tuple[str, ...] = ()
    work_modes: tuple[str, ...] = ()
    employment_options: tuple[EmploymentOption, ...] = ()
    skill_requirements: tuple[SkillRequirement, ...] = ()
