"""Run SQL data-quality checks against PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import LiteralString, cast

import psycopg
from dotenv import load_dotenv
from psycopg.sql import SQL

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_QUALITY_DIRECTORY = PROJECT_ROOT / "sql" / "quality"


@dataclass
class QualitySummary:
    """Result of one quality-check execution."""

    discovered: int = 0
    passed: int = 0
    failed: int = 0


def discover_quality_checks(directory: Path) -> list[Path]:
    """Return SQL quality checks in deterministic order."""
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.sql") if path.is_file())


def run_quality_checks(
    quality_directory: Path = DEFAULT_QUALITY_DIRECTORY,
) -> QualitySummary:
    """Run every SQL quality check in its own transaction."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    checks = discover_quality_checks(quality_directory)
    if not checks:
        raise RuntimeError(f"No SQL quality checks found in {quality_directory}")

    summary = QualitySummary(discovered=len(checks))
    with psycopg.connect(database_url) as connection:
        for check_path in checks:
            _run_check(connection, check_path, summary)
    return summary


def _run_check(
    connection: psycopg.Connection,
    check_path: Path,
    summary: QualitySummary,
) -> None:
    try:
        sql = check_path.read_text(encoding="utf-8")
        with connection.transaction():
            result = connection.execute(SQL(cast(LiteralString, sql)))
            _print_result(result)
    except (OSError, psycopg.Error) as error:
        summary.failed += 1
        print(f"[FAIL] {check_path}: {error}", file=sys.stderr)
        return

    summary.passed += 1
    print(f"[PASS] {check_path}")


def _print_result(result: psycopg.Cursor) -> None:
    if result.description is None:
        return
    columns = [column.name for column in result.description]
    print("  " + " | ".join(columns))
    for row in result.fetchall():
        print("  " + " | ".join(str(value) for value in row))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        type=Path,
        default=DEFAULT_QUALITY_DIRECTORY,
        help="Directory containing SQL quality checks.",
    )
    return parser.parse_args()


def main() -> int:
    """Run SQL quality checks."""
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    try:
        summary = run_quality_checks(args.directory)
    except (OSError, RuntimeError, psycopg.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(
        "Summary: "
        f"discovered={summary.discovered}, "
        f"passed={summary.passed}, "
        f"failed={summary.failed}"
    )
    return 1 if summary.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
