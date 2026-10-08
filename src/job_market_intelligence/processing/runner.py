"""Run source-specific parsers for all unprocessed raw runs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import psycopg
from dotenv import load_dotenv

from job_market_intelligence.ingestion.config import (
    load_toml,
    resolve_project_path,
)
from job_market_intelligence.processing.database import ProcessingRepository, utc_now
from job_market_intelligence.processing.models import ParsedJobPosting
from job_market_intelligence.processing.sources.greenhouse import GreenhouseParser
from job_market_intelligence.processing.utils import optional_text, parse_datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "ingestion.toml"
PARSER_VERSION = "v1"


class RawRunParser(Protocol):
    """Interface implemented by each source-specific parser."""

    def parse(
        self,
        response_path: Path,
        metadata: Mapping[str, Any],
    ) -> list[ParsedJobPosting]: ...


@dataclass
class ProcessingSummary:
    """Result of one parser-runner execution."""

    discovered: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    records: int = 0


def build_parser_registry(project_root: Path) -> dict[str, RawRunParser]:
    """Build source parser instances."""
    return {"greenhouse": GreenhouseParser(project_root)}


def discover_raw_runs(storage_directory: Path) -> list[Path]:
    """Find raw run directories containing both required files."""
    if not storage_directory.exists():
        return []
    return sorted(
        {
            metadata_path.parent
            for metadata_path in storage_directory.rglob("metadata.json")
            if metadata_path.with_name("response.json").is_file()
        }
    )


def run_processing(
    config_path: Path = DEFAULT_CONFIG_PATH,
    *,
    project_root: Path = PROJECT_ROOT,
    selected_sources: list[str] | None = None,
    dry_run: bool = False,
) -> ProcessingSummary:
    """Process every raw run not marked as processed."""
    configured_sources, selected_source_ids = _load_processing_config(
        config_path,
        selected_sources,
    )
    registry = build_parser_registry(project_root)
    summary = ProcessingSummary()
    if dry_run:
        return _run_dry_run(
            configured_sources,
            selected_source_ids,
            project_root,
            registry,
            summary,
        )

    _run_database_processing(
        configured_sources,
        selected_source_ids,
        project_root,
        registry,
        summary,
    )
    return summary


def _load_processing_config(
    config_path: Path,
    selected_sources: list[str] | None,
) -> tuple[list[dict[str, Any]], set[str]]:
    runner_config = load_toml(config_path)
    configured_sources = runner_config.get("sources", [])
    selected_source_ids = set(selected_sources or [])
    configured_source_ids = {entry["id"] for entry in configured_sources}
    unknown_sources = selected_source_ids - configured_source_ids
    if unknown_sources:
        names = ", ".join(sorted(unknown_sources))
        raise RuntimeError(f"Source is not present in ingestion configuration: {names}")
    return configured_sources, selected_source_ids


def _run_database_processing(
    configured_sources: list[dict[str, Any]],
    selected_source_ids: set[str],
    project_root: Path,
    registry: dict[str, RawRunParser],
    summary: ProcessingSummary,
) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    with psycopg.connect(database_url) as connection:
        repository = ProcessingRepository(connection)
        for source_entry in configured_sources:
            if _should_process_source(source_entry, selected_source_ids):
                _process_source(
                    source_entry,
                    project_root,
                    registry,
                    repository,
                    connection,
                    summary,
                )


def _should_process_source(
    source_entry: dict[str, Any],
    selected_source_ids: set[str],
) -> bool:
    source_id = source_entry["id"]
    return (not selected_source_ids or source_id in selected_source_ids) and source_entry.get(
        "enabled", True
    )


def _process_source(
    source_entry: dict[str, Any],
    project_root: Path,
    registry: dict[str, RawRunParser],
    repository: ProcessingRepository,
    connection: psycopg.Connection[Any],
    summary: ProcessingSummary,
) -> None:
    source_id = source_entry["id"]
    parser = registry.get(source_id)
    if parser is None:
        raise RuntimeError(f"No parser is registered for source: {source_id}")

    source_config = load_toml(resolve_project_path(project_root, source_entry["config_path"]))
    storage_directory = resolve_project_path(
        project_root,
        source_config["storage"]["directory"],
    )
    for run_directory in discover_raw_runs(storage_directory):
        summary.discovered += 1
        _process_run(
            repository,
            connection,
            parser,
            source_id,
            run_directory,
            project_root,
            summary,
        )


def _run_dry_run(
    configured_sources: list[dict[str, Any]],
    selected_source_ids: set[str],
    project_root: Path,
    registry: dict[str, RawRunParser],
    summary: ProcessingSummary,
) -> ProcessingSummary:
    for source_entry in configured_sources:
        source_id = source_entry["id"]
        if selected_source_ids and source_id not in selected_source_ids:
            continue
        if not source_entry.get("enabled", True):
            continue
        parser = registry.get(source_id)
        if parser is None:
            raise RuntimeError(f"No parser is registered for source: {source_id}")
        source_config = load_toml(resolve_project_path(project_root, source_entry["config_path"]))
        storage_directory = resolve_project_path(
            project_root,
            source_config["storage"]["directory"],
        )
        for run_directory in discover_raw_runs(storage_directory):
            summary.discovered += 1
            print(f"[{source_id}] {run_directory}")
    return summary


def _process_run(
    repository: ProcessingRepository,
    connection: psycopg.Connection[Any],
    parser: RawRunParser,
    source_id: str,
    run_directory: Path,
    project_root: Path,
    summary: ProcessingSummary,
) -> None:
    metadata = _load_metadata(run_directory / "metadata.json")
    run_id = _required_metadata_text(metadata, "run_id")
    metadata_source_id = _required_metadata_text(metadata, "source_id")
    if metadata_source_id != source_id:
        raise RuntimeError(
            f"Raw run source mismatch: config={source_id}, metadata={metadata_source_id}"
        )

    status = repository.register_raw_run(
        source_id=source_id,
        run_id=run_id,
        raw_path=run_directory.relative_to(project_root),
        retrieved_at=parse_datetime(metadata.get("retrieved_at")),
        record_count=_optional_int(metadata.get("record_count")),
        payload_sha256=optional_text(metadata.get("payload_sha256")),
    )
    connection.commit()
    if status == "processed":
        summary.skipped += 1
        return

    repository.mark_processing(source_id, run_id)
    connection.commit()
    try:
        records = parser.parse(run_directory / "response.json", metadata)
        retrieved_at = parse_datetime(metadata.get("retrieved_at")) or utc_now()
        with connection.transaction():
            summary.records += repository.upsert_job_postings(
                records,
                retrieved_at,
                PARSER_VERSION,
            )
            repository.mark_processed(source_id, run_id, len(records), PARSER_VERSION)
        summary.processed += 1
        print(f"[{source_id}] processed {run_id}: {len(records)} records")
    except Exception as error:
        connection.rollback()
        repository.mark_failed(source_id, run_id, str(error))
        connection.commit()
        summary.failed += 1
        print(f"[{source_id}] failed {run_id}: {error}", file=sys.stderr)


def _load_metadata(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Metadata must be a JSON object: {path}")
    return payload


def _required_metadata_text(metadata: Mapping[str, Any], key: str) -> str:
    value = optional_text(metadata.get(key))
    if not value:
        raise ValueError(f"Metadata field is missing: {key}")
    return value


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--source",
        action="append",
        dest="selected_sources",
        help="Process only this configured source; may be repeated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List discovered raw runs without connecting to PostgreSQL.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the raw-data parser."""
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    try:
        summary = run_processing(
            args.config,
            project_root=PROJECT_ROOT,
            selected_sources=args.selected_sources,
            dry_run=args.dry_run,
        )
    except (OSError, RuntimeError, ValueError, psycopg.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(
        "Summary: "
        f"discovered={summary.discovered}, "
        f"processed={summary.processed}, "
        f"skipped={summary.skipped}, "
        f"failed={summary.failed}, "
        f"records={summary.records}"
    )
    return 1 if summary.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
