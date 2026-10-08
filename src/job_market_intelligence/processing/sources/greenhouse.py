"""Parse Greenhouse Job Board API responses into normalized records."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from job_market_intelligence.processing.extraction import extract_hours
from job_market_intelligence.processing.models import (
    EmploymentOption,
    ParsedJobPosting,
    SkillRequirement,
)
from job_market_intelligence.processing.normalization import NormalizationDictionaries
from job_market_intelligence.processing.utils import optional_text, parse_datetime


class GreenhouseParser:
    """Parse one stored Greenhouse raw run."""

    def __init__(self, project_root: Path) -> None:
        self.normalizer = NormalizationDictionaries.from_project_root(project_root)

    def parse(
        self,
        response_path: Path,
        metadata: Mapping[str, Any],
    ) -> list[ParsedJobPosting]:
        """Parse a stored response file."""
        payload = json.loads(response_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ValueError(f"Greenhouse response has no jobs array: {response_path}")

        context = metadata.get("context") or {}
        default_company = str(context.get("company") or "")
        return [self.parse_job(job, default_company) for job in payload["jobs"]]

    def parse_job(
        self,
        job: Mapping[str, Any],
        default_company: str,
    ) -> ParsedJobPosting:
        """Parse one Greenhouse job object."""
        source_job_id = job.get("id")
        if source_job_id is None:
            raise ValueError("Greenhouse job has no id")

        title = str(job.get("title") or "")
        content = str(job.get("content") or "")
        search_text = f"{title}\n{content}"
        company_text = str(job.get("company_name") or default_company)
        company_name = self.normalizer.companies.find_first(company_text) or company_text
        if not company_name:
            raise ValueError(f"Greenhouse job {source_job_id} has no company")

        return ParsedJobPosting(
            source_job_id=str(source_job_id),
            company_name=company_name,
            role_name=(
                self.normalizer.roles.find_first(title)
                or self.normalizer.roles.find_first(search_text)
            ),
            seniority_level_name=(
                self.normalizer.seniority_levels.find_first(title)
                or self.normalizer.seniority_levels.find_first(search_text)
            ),
            source_url=optional_text(job.get("absolute_url")),
            source_published_at=parse_datetime(job.get("first_published")),
            source_updated_at=parse_datetime(job.get("updated_at")),
            raw_advertisement=dict(job),
            locations=self._normalize_locations(job),
            work_modes=self._normalize_work_modes(job, search_text),
            employment_options=tuple(self._normalize_employment_options(job, search_text)),
            skill_requirements=tuple(
                SkillRequirement(name=skill_name)
                for skill_name in self.normalizer.skills.find_all(search_text)
            ),
        )

    def _normalize_locations(self, job: Mapping[str, Any]) -> tuple[str, ...]:
        location_texts: list[str] = []
        location = job.get("location")
        if isinstance(location, Mapping):
            name = optional_text(location.get("name"))
            if name:
                location_texts.append(name)
        offices = job.get("offices")
        if isinstance(offices, list):
            location_texts.extend(
                text
                for office in offices
                if isinstance(office, Mapping)
                for text in [optional_text(office.get("location"))]
                if text
            )

        return tuple(
            dict.fromkeys(
                location_name
                for location_text in location_texts
                for location_name in self.normalizer.locations.find_non_overlapping(location_text)
            )
        )

    def _normalize_work_modes(
        self,
        job: Mapping[str, Any],
        search_text: str,
    ) -> tuple[str, ...]:
        metadata_text = " ".join(_metadata_values(job, "location type"))
        matches = self.normalizer.work_modes.find_all(metadata_text)
        if not matches:
            matches = self.normalizer.work_modes.find_all(search_text)
        return matches

    def _normalize_employment_options(
        self,
        job: Mapping[str, Any],
        search_text: str,
    ) -> list[EmploymentOption]:
        employment_text = " ".join(_metadata_values(job, "employment type"))
        relation_name = self.normalizer.employment_relations.find_first(employment_text)
        workload_name = self.normalizer.workloads.find_first(f"{employment_text}\n{search_text}")
        hours_min, hours_max, hours_period = extract_hours(search_text)
        if not any((relation_name, workload_name, hours_min, hours_max, hours_period)):
            return []

        return [
            EmploymentOption(
                employment_relation_name=relation_name,
                workload_name=workload_name,
                hours_min=hours_min,
                hours_max=hours_max,
                hours_period=hours_period,
            )
        ]


def _metadata_values(job: Mapping[str, Any], field_name: str) -> list[str]:
    metadata = job.get("metadata")
    if not isinstance(metadata, list):
        return []

    values: list[str] = []
    for item in metadata:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name") or "").casefold().rstrip(":")
        if name != field_name.casefold().rstrip(":"):
            continue
        value = item.get("value")
        if isinstance(value, list):
            values.extend(str(entry) for entry in value)
        elif value is not None:
            values.append(str(value))
    return values
