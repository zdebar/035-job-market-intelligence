"""PostgreSQL writes for parsed raw job advertisements."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from psycopg import Connection
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb

from job_market_intelligence.processing.models import ParsedJobPosting


class ProcessingRepository:
    """Persist processing state and normalized job postings."""

    def __init__(self, connection: Connection[Any]) -> None:
        self.connection = connection

    def register_raw_run(
        self,
        *,
        source_id: str,
        run_id: str,
        raw_path: Path,
        retrieved_at: datetime | None,
        record_count: int | None,
        payload_sha256: str | None,
    ) -> str:
        """Register a run and return its current processing status."""
        self.connection.execute(
            """
            INSERT INTO raw_ingestion_runs (
                source_id,
                run_id,
                raw_path,
                retrieved_at,
                record_count,
                payload_sha256
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, run_id) DO NOTHING
            """,
            (
                source_id,
                run_id,
                raw_path.as_posix(),
                retrieved_at,
                record_count,
                payload_sha256,
            ),
        )
        row = self.connection.execute(
            """
            SELECT status
            FROM raw_ingestion_runs
            WHERE source_id = %s AND run_id = %s
            """,
            (source_id, run_id),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Raw run was not registered: {source_id}/{run_id}")
        return str(row[0])

    def mark_processing(self, source_id: str, run_id: str) -> None:
        """Mark a raw run as currently being parsed."""
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'processing',
                processing_started_at = now(),
                updated_at = now(),
                error_message = NULL
            WHERE source_id = %s AND run_id = %s
            """,
            (source_id, run_id),
        )

    def mark_processed(
        self,
        source_id: str,
        run_id: str,
        processed_records: int,
        parser_version: str,
    ) -> None:
        """Mark a raw run as successfully parsed."""
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'processed',
                processed_records = %s,
                parser_version = %s,
                processed_at = now(),
                updated_at = now(),
                error_message = NULL
            WHERE source_id = %s AND run_id = %s
            """,
            (processed_records, parser_version, source_id, run_id),
        )

    def mark_failed(self, source_id: str, run_id: str, error_message: str) -> None:
        """Mark a raw run as failed and retain a short diagnostic."""
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'failed',
                error_message = %s,
                updated_at = now()
            WHERE source_id = %s AND run_id = %s
            """,
            (error_message[:2000], source_id, run_id),
        )

    def upsert_job_postings(
        self,
        records: list[ParsedJobPosting],
        retrieved_at: datetime,
        normalization_version: str,
    ) -> int:
        """Upsert all parsed postings from one raw run."""
        for record in records:
            self._upsert_job_posting(record, retrieved_at, normalization_version)
        return len(records)

    def _upsert_job_posting(
        self,
        record: ParsedJobPosting,
        retrieved_at: datetime,
        normalization_version: str,
    ) -> None:
        source_id = self._required_id("sources", record.company_name)
        company_id = self._required_id("companies", record.company_name)
        role_id = self._optional_id("roles", record.role_name)
        seniority_level_id = self._optional_id("seniority_levels", record.seniority_level_name)
        row = self.connection.execute(
            """
            INSERT INTO job_postings (
                source_id,
                source_job_id,
                company_id,
                role_id,
                seniority_level_id,
                raw_advertisement,
                source_url,
                source_published_at,
                source_updated_at,
                retrieved_at,
                last_seen_at,
                status,
                normalization_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s)
            ON CONFLICT (source_id, source_job_id) DO UPDATE SET
                company_id = EXCLUDED.company_id,
                role_id = EXCLUDED.role_id,
                seniority_level_id = EXCLUDED.seniority_level_id,
                raw_advertisement = EXCLUDED.raw_advertisement,
                source_url = EXCLUDED.source_url,
                source_published_at = EXCLUDED.source_published_at,
                source_updated_at = EXCLUDED.source_updated_at,
                retrieved_at = EXCLUDED.retrieved_at,
                last_seen_at = EXCLUDED.last_seen_at,
                status = 'active',
                normalization_version = EXCLUDED.normalization_version,
                updated_at = now()
            RETURNING id
            """,
            (
                source_id,
                record.source_job_id,
                company_id,
                role_id,
                seniority_level_id,
                Jsonb(record.raw_advertisement),
                record.source_url,
                record.source_published_at,
                record.source_updated_at,
                retrieved_at,
                retrieved_at,
                normalization_version,
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Could not save job {record.source_job_id}")

        job_posting_id = int(row[0])
        self._replace_child_records(job_posting_id, record)
        self._ensure_canonical_job(job_posting_id)

    def _replace_child_records(
        self,
        job_posting_id: int,
        record: ParsedJobPosting,
    ) -> None:
        for table in (
            "job_posting_locations",
            "job_posting_work_modes",
            "job_posting_employment_options",
            "job_posting_compensations",
            "job_skill_requirements",
        ):
            self.connection.execute(
                SQL("DELETE FROM {} WHERE job_posting_id = %s").format(Identifier(table)),
                (job_posting_id,),
            )

        for location_name in record.locations:
            location_id = self._required_id("locations", location_name)
            self.connection.execute(
                """
                INSERT INTO job_posting_locations (job_posting_id, location_id)
                VALUES (%s, %s)
                """,
                (job_posting_id, location_id),
            )

        for work_mode_name in record.work_modes:
            work_mode_id = self._required_id("work_modes", work_mode_name)
            self.connection.execute(
                """
                INSERT INTO job_posting_work_modes (job_posting_id, work_mode_id)
                VALUES (%s, %s)
                """,
                (job_posting_id, work_mode_id),
            )

        for option in record.employment_options:
            employment_relation_id = self._optional_id(
                "employment_relations", option.employment_relation_name
            )
            workload_id = self._optional_id("workloads", option.workload_name)
            self.connection.execute(
                """
                INSERT INTO job_posting_employment_options (
                    job_posting_id,
                    employment_relation_id,
                    workload_id,
                    hours_min,
                    hours_max,
                    hours_period
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    job_posting_id,
                    employment_relation_id,
                    workload_id,
                    option.hours_min,
                    option.hours_max,
                    option.hours_period,
                ),
            )

        for compensation in record.compensation_options:
            employment_relation_id = self._optional_id(
                "employment_relations",
                compensation.employment_relation_name,
            )
            self.connection.execute(
                """
                INSERT INTO job_posting_compensations (
                    job_posting_id,
                    employment_relation_id,
                    salary_min,
                    salary_max,
                    salary_currency,
                    salary_period
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    job_posting_id,
                    employment_relation_id,
                    compensation.salary_min,
                    compensation.salary_max,
                    compensation.salary_currency,
                    compensation.salary_period,
                ),
            )

        for requirement in record.skill_requirements:
            skill_id = self._required_id("skills", requirement.name)
            proficiency_level_id = self._optional_id(
                "proficiency_levels", requirement.proficiency_level_name
            )
            requirement_type_id = self._optional_id(
                "requirement_types", requirement.requirement_type_name
            )
            self.connection.execute(
                """
                INSERT INTO job_skill_requirements (
                    job_posting_id,
                    skill_id,
                    proficiency_level_id,
                    requirement_type_id,
                    priority
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    job_posting_id,
                    skill_id,
                    proficiency_level_id,
                    requirement_type_id,
                    requirement.priority,
                ),
            )

    def _ensure_canonical_job(self, job_posting_id: int) -> None:
        row = self.connection.execute(
            """
            SELECT canonical_job_id
            FROM job_posting_sources
            WHERE job_posting_id = %s
            """,
            (job_posting_id,),
        ).fetchone()
        if row is not None:
            return

        canonical_job = self.connection.execute(
            "INSERT INTO canonical_jobs DEFAULT VALUES RETURNING id"
        ).fetchone()
        if canonical_job is None:
            raise RuntimeError(f"Could not create canonical job for {job_posting_id}")
        self.connection.execute(
            """
            INSERT INTO job_posting_sources (canonical_job_id, job_posting_id)
            VALUES (%s, %s)
            """,
            (canonical_job[0], job_posting_id),
        )

    def _required_id(self, table_name: str, name: str) -> int:
        value = self._optional_id(table_name, name)
        if value is None:
            raise ValueError(f"Missing reference value in {table_name}: {name}")
        return value

    def _optional_id(self, table_name: str, name: str | None) -> int | None:
        if not name:
            return None
        row = self.connection.execute(
            SQL("SELECT id FROM {} WHERE name = %s").format(Identifier(table_name)),
            (name,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown reference value in {table_name}: {name}")
        return int(row[0])


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)
