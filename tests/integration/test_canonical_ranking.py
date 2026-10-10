import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

from job_market_intelligence.processing.database import ProcessingRepository
from job_market_intelligence.processing.fingerprint import content_fingerprint
from job_market_intelligence.processing.models import ParsedJobPosting

PROJECT_ROOT = Path(__file__).parents[2]


def _connection() -> psycopg.Connection:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url)

    required = {
        "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "port": os.getenv("POSTGRES_PORT"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "dbname": os.getenv("POSTGRES_DB"),
    }
    if any(value is None for value in required.values()):
        pytest.skip("Local PostgreSQL connection is not configured")
    return psycopg.connect(**required)


@pytest.fixture
def repository() -> Generator[ProcessingRepository, None, None]:
    connection = _connection()
    try:
        yield ProcessingRepository(connection)
    finally:
        connection.rollback()
        connection.close()


def _posting(source_job_id: str, updated_at: datetime) -> ParsedJobPosting:
    description = "<p>Build data pipelines with Python and SQL.</p>"
    return ParsedJobPosting(
        source_job_id=source_job_id,
        company_name="Ataccama",
        role_name="Data Engineer",
        seniority_level_name=None,
        source_url=f"https://jobs.example/{source_job_id}",
        source_published_at=updated_at,
        source_updated_at=updated_at,
        raw_advertisement={"description": description},
        content_fingerprint=content_fingerprint(description),
        locations=("Prague, Czechia",),
    )


def test_same_company_postings_from_different_sources_share_canonical_job(
    repository: ProcessingRepository,
) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    older = now - timedelta(days=1)

    first_id = repository.upsert_job_posting(
        _posting("fixture-lever-collision", older),
        "lever_ataccama",
        older,
        "test",
    )
    second_id = repository.upsert_job_posting(
        _posting("fixture-greenhouse-collision", now),
        "greenhouse_mews",
        now,
        "test",
    )

    rows = repository.connection.execute(
        """
        SELECT canonical_job_id, job_posting_id, selection_rank
        FROM job_posting_sources
        WHERE job_posting_id IN (%s, %s)
        ORDER BY selection_rank
        """,
        (first_id, second_id),
    ).fetchall()

    assert len(rows) == 2
    assert rows[0][0] == rows[1][0]
    assert rows[0][1] == second_id
    assert rows[0][2] == 1
    assert rows[1][1] == first_id
    assert rows[1][2] == 2

    repository.mark_missing_postings_inactive("lever_ataccama", now)

    inactive_rank = repository.connection.execute(
        "SELECT selection_rank FROM job_posting_sources WHERE job_posting_id = %s",
        (first_id,),
    ).fetchone()
    active_rank = repository.connection.execute(
        "SELECT selection_rank FROM job_posting_sources WHERE job_posting_id = %s",
        (second_id,),
    ).fetchone()

    assert inactive_rank == (None,)
    assert active_rank == (1,)
