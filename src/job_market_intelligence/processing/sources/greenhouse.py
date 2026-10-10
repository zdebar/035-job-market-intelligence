"""Parse Greenhouse Job Board API responses into normalized records."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from job_market_intelligence.processing.fingerprint import content_fingerprint
from job_market_intelligence.processing.models import (
    EmploymentOption,
    ParsedJobPosting,
    ParseResult,
    RecordError,
)
from job_market_intelligence.processing.sources.common import ParserSupport
from job_market_intelligence.processing.utils import optional_text, parse_datetime


class GreenhouseParser:
    """Parse one stored Greenhouse raw run."""

    def __init__(self, project_root: Path) -> None:
        self.support = ParserSupport(project_root)

    def parse(
        self,
        response_path: Path,
        metadata: Mapping[str, Any],
    ) -> ParseResult:
        """Parse a stored response file."""
        payload = json.loads(response_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ValueError(f"Greenhouse response has no jobs array: {response_path}")

        context = metadata.get("context") or {}
        default_company = str(context.get("company") or "")
        records: list[ParsedJobPosting] = []
        errors: list[RecordError] = []
        for job in payload["jobs"]:
            source_job_id = optional_text(job.get("id")) if isinstance(job, Mapping) else None
            try:
                records.append(self.parse_job(job, default_company))
            except (TypeError, ValueError, KeyError) as error:
                errors.append(
                    RecordError(
                        source_job_id=source_job_id,
                        stage="parse",
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )
                )
        return ParseResult(tuple(records), tuple(errors))

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
        company_name = self.support.company_name(company_text, default_company)

        return ParsedJobPosting(
            source_job_id=str(source_job_id),
            company_name=company_name,
            role_name=(
                self.support.normalizer.roles.find_first(title)
                or self.support.normalizer.roles.find_first(search_text)
            ),
            seniority_level_name=(
                self.support.normalizer.seniority_levels.find_first(title)
                or self.support.normalizer.seniority_levels.find_first(search_text)
            ),
            source_url=optional_text(job.get("absolute_url")),
            source_published_at=parse_datetime(job.get("first_published")),
            source_updated_at=parse_datetime(job.get("updated_at")),
            raw_advertisement=dict(job),
            content_fingerprint=content_fingerprint(content) if content else None,
            locations=self._normalize_locations(job),
            work_modes=self._normalize_work_modes(job, search_text),
            employment_options=self._normalize_employment_options(job, search_text),
            skill_requirements=self.support.skills(search_text),
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
                for location_name in self.support.normalizer.locations.find_non_overlapping(
                    location_text
                )
            )
        )

    def _normalize_work_modes(
        self,
        job: Mapping[str, Any],
        search_text: str,
    ) -> tuple[str, ...]:
        metadata_text = " ".join(_metadata_values(job, "location type"))
        return self.support.work_modes(metadata_text, search_text)

    def _normalize_employment_options(
        self,
        job: Mapping[str, Any],
        search_text: str,
    ) -> tuple[EmploymentOption, ...]:
        employment_text = " ".join(_metadata_values(job, "employment type"))
        return self.support.employment_options(employment_text, search_text)


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
