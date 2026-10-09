"""PostgreSQL writes for parsed raw job advertisements."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from psycopg import Connection
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb

from job_market_intelligence.processing.models import (
    ParsedJobPosting,
    RecordError,
)


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
        """Register a run and return its current status."""
        self.connection.execute(
            """
            INSERT INTO raw_ingestion_runs (
                source_id, run_id, raw_path, retrieved_at, record_count, payload_sha256
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
            SET status = 'processing', processing_started_at = now(),
                updated_at = now(), error_message = NULL, processed_records = 0
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
        """Mark a fully successful raw run."""
        self._mark_run(
            source_id,
            run_id,
            "processed",
            processed_records,
            parser_version,
            None,
        )

    def mark_partial(
        self,
        source_id: str,
        run_id: str,
        processed_records: int,
        parser_version: str,
        error_message: str,
    ) -> None:
        """Mark a run where only some records were processed."""
        self._mark_run(
            source_id,
            run_id,
            "partial",
            processed_records,
            parser_version,
            error_message,
        )

    def mark_failed(self, source_id: str, run_id: str, error_message: str) -> None:
        """Mark a run as failed and retain a short diagnostic."""
        self._mark_run(source_id, run_id, "failed", 0, None, error_message)

    def _mark_run(
        self,
        source_id: str,
        run_id: str,
        status: str,
        processed_records: int,
        parser_version: str | None,
        error_message: str | None,
    ) -> None:
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = %s, processed_records = %s, parser_version = COALESCE(%s, parser_version),
                processed_at = CASE WHEN %s IN ('processed', 'partial') THEN now() ELSE processed_at END,
                updated_at = now(), error_message = %s
            WHERE source_id = %s AND run_id = %s
            """,
            (
                status,
                processed_records,
                parser_version,
                status,
                error_message[:2000] if error_message else None,
                source_id,
                run_id,
            ),
        )

    def record_error(
        self,
        source_id: str,
        run_id: str,
        error: RecordError,
    ) -> None:
        """Store one record-level error without replacing previous attempts."""
        self.connection.execute(
            """
            INSERT INTO raw_ingestion_record_errors (
                raw_ingestion_run_id, source_job_id, stage, error_type, error_message
            )
            SELECT id, %s, %s, %s, %s
            FROM raw_ingestion_runs
            WHERE source_id = %s AND run_id = %s
            """,
            (
                error.source_job_id,
                error.stage,
                error.error_type,
                error.error_message[:2000],
                source_id,
                run_id,
            ),
        )

    def upsert_job_posting(
        self,
        record: ParsedJobPosting,
        source_key: str,
        retrieved_at: datetime,
        normalization_version: str,
    ) -> int:
        """Upsert one posting and preserve or create its canonical job link."""
        source_id = self._required_source_id(source_key)
        company_id = self._required_id("companies", "name", record.company_name)
        role_id = self._optional_id("roles", "name", record.role_name)
        seniority_level_id = self._optional_id(
            "seniority_levels", "name", record.seniority_level_name
        )
        row = self.connection.execute(
            """
            INSERT INTO job_postings (
                source_id, source_job_id, company_id, role_id, seniority_level_id,
                raw_advertisement, content_fingerprint, source_url, source_published_at,
                source_updated_at, retrieved_at, last_seen_at, status, normalization_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s)
            ON CONFLICT (source_id, source_job_id) DO UPDATE SET
                company_id = EXCLUDED.company_id,
                role_id = EXCLUDED.role_id,
                seniority_level_id = EXCLUDED.seniority_level_id,
                raw_advertisement = EXCLUDED.raw_advertisement,
                content_fingerprint = EXCLUDED.content_fingerprint,
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
                record.content_fingerprint,
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
        return job_posting_id

    def _replace_child_records(self, job_posting_id: int, record: ParsedJobPosting) -> None:
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
            location_id = self._required_id("locations", "name", location_name)
            self.connection.execute(
                "INSERT INTO job_posting_locations (job_posting_id, location_id) VALUES (%s, %s)",
                (job_posting_id, location_id),
            )

        for work_mode_name in record.work_modes:
            work_mode_id = self._required_id("work_modes", "name", work_mode_name)
            self.connection.execute(
                "INSERT INTO job_posting_work_modes (job_posting_id, work_mode_id) VALUES (%s, %s)",
                (job_posting_id, work_mode_id),
            )

        for option in record.employment_options:
            relation_id = self._optional_id(
                "employment_relations", "name", option.employment_relation_name
            )
            workload_id = self._optional_id("workloads", "name", option.workload_name)
            self.connection.execute(
                """
                INSERT INTO job_posting_employment_options (
                    job_posting_id, employment_relation_id, workload_id,
                    hours_min, hours_max, hours_period
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    job_posting_id,
                    relation_id,
                    workload_id,
                    option.hours_min,
                    option.hours_max,
                    option.hours_period,
                ),
            )

        for compensation in record.compensation_options[:1]:
            self.connection.execute(
                """
                INSERT INTO job_posting_compensations (
                    job_posting_id, salary_min, salary_max, salary_currency, salary_period
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    job_posting_id,
                    compensation.salary_min,
                    compensation.salary_max,
                    compensation.salary_currency,
                    compensation.salary_period,
                ),
            )

        for requirement in record.skill_requirements:
            skill_id = self._required_id("skills", "name", requirement.name)
            proficiency_id = self._optional_id(
                "proficiency_levels", "name", requirement.proficiency_level_name
            )
            requirement_type_id = self._optional_id(
                "requirement_types", "name", requirement.requirement_type_name
            )
            self.connection.execute(
                """
                INSERT INTO job_skill_requirements (
                    job_posting_id, skill_id, proficiency_level_id,
                    requirement_type_id, priority
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    job_posting_id,
                    skill_id,
                    proficiency_id,
                    requirement_type_id,
                    requirement.priority,
                ),
            )

    def _ensure_canonical_job(self, job_posting_id: int) -> None:
        existing = self.connection.execute(
            "SELECT canonical_job_id FROM job_posting_sources WHERE job_posting_id = %s",
            (job_posting_id,),
        ).fetchone()
        if existing is not None:
            return

        canonical_id = self._find_canonical_match(job_posting_id)
        match_method = "algorithmic_match" if canonical_id is not None else "new_canonical_job"
        if canonical_id is None:
            row = self.connection.execute(
                "INSERT INTO canonical_jobs DEFAULT VALUES RETURNING id"
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Could not create canonical job for {job_posting_id}")
            canonical_id = int(row[0])

        self.connection.execute(
            """
            INSERT INTO job_posting_sources (
                canonical_job_id, job_posting_id, match_method, matched_at
            ) VALUES (%s, %s, %s, now())
            """,
            (canonical_id, job_posting_id, match_method),
        )

    def _find_canonical_match(self, job_posting_id: int) -> int | None:
        current = self.connection.execute(
            """
            SELECT company_id, role_id, seniority_level_id, content_fingerprint
            FROM job_postings
            WHERE id = %s
            """,
            (job_posting_id,),
        ).fetchone()
        if current is None:
            raise RuntimeError(f"Posting does not exist: {job_posting_id}")
        company_id, role_id, seniority_id, fingerprint = current

        if fingerprint:
            exact = self._fingerprint_candidates(job_posting_id, company_id, fingerprint)
            if len(exact) == 1:
                return exact[0]
            if exact:
                return None

        if role_id is None or not self._has_locations(job_posting_id):
            return None
        fallback = self._fallback_candidates(
            job_posting_id,
            company_id,
            role_id,
            seniority_id,
        )
        return fallback[0] if len(fallback) == 1 else None

    def _fingerprint_candidates(
        self,
        job_posting_id: int,
        company_id: int,
        fingerprint: str,
    ) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT links.canonical_job_id
            FROM job_postings postings
            JOIN job_posting_sources links ON links.job_posting_id = postings.id
            WHERE postings.id <> %s
              AND postings.company_id = %s
              AND postings.content_fingerprint = %s
            """,
            (job_posting_id, company_id, fingerprint),
        ).fetchall()
        return [int(row[0]) for row in rows]

    def _fallback_candidates(
        self,
        job_posting_id: int,
        company_id: int,
        role_id: int,
        seniority_id: int | None,
    ) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT links.canonical_job_id
            FROM job_postings postings
            JOIN job_posting_sources links ON links.job_posting_id = postings.id
            WHERE postings.id <> %s
              AND postings.company_id = %s
              AND postings.role_id = %s
              AND (
                  postings.seniority_level_id IS NULL
                  OR CAST(%s AS BIGINT) IS NULL
                  OR postings.seniority_level_id = CAST(%s AS BIGINT)
              )
              AND ARRAY(
                  SELECT location_id
                  FROM job_posting_locations
                  WHERE job_posting_id = postings.id
                  ORDER BY location_id
              ) = ARRAY(
                  SELECT location_id
                  FROM job_posting_locations
                  WHERE job_posting_id = %s
                  ORDER BY location_id
              )
            """,
            (
                job_posting_id,
                company_id,
                role_id,
                seniority_id,
                seniority_id,
                job_posting_id,
            ),
        ).fetchall()
        return [int(row[0]) for row in rows]

    def _has_locations(self, job_posting_id: int) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM job_posting_locations WHERE job_posting_id = %s LIMIT 1",
            (job_posting_id,),
        ).fetchone()
        return row is not None

    def mark_missing_postings_inactive(
        self,
        source_key: str,
        retrieved_at: datetime,
    ) -> int:
        """Deactivate postings absent from a fully successful board download."""
        source_id = self._required_source_id(source_key)
        result = self.connection.execute(
            """
            UPDATE job_postings
            SET status = 'inactive', updated_at = now()
            WHERE source_id = %s
              AND status = 'active'
              AND last_seen_at < %s
            """,
            (source_id, retrieved_at),
        )
        return result.rowcount

    def _required_source_id(self, source_key: str) -> int:
        value = self._optional_id("sources", "source_key", source_key)
        if value is None:
            raise ValueError(f"Unknown source key: {source_key}")
        return value

    def _required_id(self, table_name: str, column_name: str, value: str | None) -> int:
        result = self._optional_id(table_name, column_name, value)
        if result is None:
            raise ValueError(f"Missing reference value in {table_name}: {value}")
        return result

    def _optional_id(
        self,
        table_name: str,
        column_name: str,
        value: str | None,
    ) -> int | None:
        if not value:
            return None
        row = self.connection.execute(
            SQL("SELECT id FROM {} WHERE {} = %s").format(
                Identifier(table_name), Identifier(column_name)
            ),
            (value,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown reference value in {table_name}: {value}")
        return int(row[0])


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)
