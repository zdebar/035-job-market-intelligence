"""Parse Ashby public job-board responses."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from job_market_intelligence.processing.fingerprint import content_fingerprint
from job_market_intelligence.processing.models import (
    CompensationOption,
    ParsedJobPosting,
    ParseResult,
    RecordError,
)
from job_market_intelligence.processing.sources.common import (
    ParserSupport,
    decimal_value,
    salary_period,
    text_value,
)
from job_market_intelligence.processing.utils import optional_text, parse_datetime


class AshbyParser:
    """Parse one stored Ashby raw run."""

    def __init__(self, project_root: Path) -> None:
        self.support = ParserSupport(project_root)

    def parse(self, response_path: Path, metadata: Mapping[str, Any]) -> ParseResult:
        payload = json.loads(response_path.read_text(encoding="utf-8"))
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list) or not all(isinstance(job, Mapping) for job in jobs):
            raise ValueError(f"Ashby response has no jobs array: {response_path}")
        context = metadata.get("context") or {}
        default_company = str(context.get("company") or "")
        records: list[ParsedJobPosting] = []
        errors: list[RecordError] = []
        for job in jobs:
            source_job_id = optional_text(job.get("id"))
            try:
                records.append(self.parse_job(job, default_company))
            except (TypeError, ValueError, KeyError) as error:
                errors.append(RecordError(source_job_id, "parse", type(error).__name__, str(error)))
        return ParseResult(tuple(records), tuple(errors))

    def parse_job(self, job: Mapping[str, Any], default_company: str) -> ParsedJobPosting:
        source_job_id = optional_text(job.get("id")) or optional_text(job.get("jobUrl"))
        if not source_job_id:
            raise ValueError("Ashby job has no id")
        title = optional_text(job.get("title")) or ""
        description = text_value(
            job.get("descriptionPlain") or job.get("descriptionHtml") or job.get("description")
        )
        search_text = f"{title}\n{description}"
        locations = [job.get("location"), job.get("secondaryLocations")]
        workplace_text = text_value(job.get("workplaceType"))
        if job.get("isRemote"):
            workplace_text = f"{workplace_text} Remote"
        employment_text = text_value(job.get("employmentType"))
        return ParsedJobPosting(
            source_job_id=source_job_id,
            company_name=self.support.company_name(job.get("company"), default_company),
            role_name=self.support.normalizer.roles.find_first(title)
            or self.support.normalizer.roles.find_first(search_text),
            seniority_level_name=self.support.normalizer.seniority_levels.find_first(title)
            or self.support.normalizer.seniority_levels.find_first(search_text),
            source_url=optional_text(job.get("jobUrl") or job.get("applyUrl")),
            source_published_at=parse_datetime(job.get("publishedAt")),
            source_updated_at=parse_datetime(job.get("updatedAt")),
            raw_advertisement=dict(job),
            content_fingerprint=content_fingerprint(description) if description else None,
            locations=self.support.locations(locations),
            work_modes=self.support.work_modes(workplace_text, search_text),
            employment_options=self.support.employment_options(employment_text, search_text),
            compensation_options=_compensations(job),
            skill_requirements=self.support.skills(search_text),
        )


def _compensations(job: Mapping[str, Any]) -> tuple[CompensationOption, ...]:
    options: list[CompensationOption] = []
    compensation = job.get("compensation")
    if not isinstance(compensation, Mapping):
        return tuple(options)
    salary = compensation.get("compensationRange") or compensation.get("range")
    if not isinstance(salary, Mapping):
        return tuple(options)
    minimum = decimal_value(salary.get("minValue") or salary.get("min"))
    maximum = decimal_value(salary.get("maxValue") or salary.get("max"))
    if minimum is None and maximum is None:
        return tuple(options)
    options.append(
        CompensationOption(
            salary_min=minimum,
            salary_max=maximum,
            salary_currency=(optional_text(salary.get("currency")) or "").upper() or None,
            salary_period=salary_period(
                salary.get("salaryType") or salary.get("interval") or salary.get("period")
            ),
        ),
    )
    return tuple(options)
