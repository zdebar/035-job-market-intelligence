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

from job_market_intelligence.ingestion.config import load_toml, resolve_project_path
from job_market_intelligence.processing.database import ProcessingRepository, utc_now
from job_market_intelligence.processing.models import ParseResult, RecordError
from job_market_intelligence.processing.sources.ashby import AshbyParser
from job_market_intelligence.processing.sources.greenhouse import GreenhouseParser
from job_market_intelligence.processing.sources.lever import LeverParser
from job_market_intelligence.processing.utils import optional_text, parse_datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "ingestion.toml"
PARSER_VERSION = "v2"


class RawRunParser(Protocol):
    """Interface implemented by each source-specific parser."""

    def parse(
        self,
        response_path: Path,
        metadata: Mapping[str, Any],
    ) -> ParseResult: ...


@dataclass(frozen=True)
class SourceContext:
    """Configured adapter and its raw storage."""

    adapter_id: str
    parser: RawRunParser
    run_directories: list[Path]
    source_config: dict[str, Any]


@dataclass
class ProcessingSummary:
    """Result of one parser-runner execution."""

    discovered: int = 0
    processed: int = 0
    partial: int = 0
    skipped: int = 0
    failed: int = 0
    records: int = 0


def build_parser_registry(project_root: Path) -> dict[str, RawRunParser]:
    """Build source parser instances."""
    return {
        "greenhouse": GreenhouseParser(project_root),
        "lever": LeverParser(project_root),
        "ashby": AshbyParser(project_root),
    }


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
    retry_partial: bool = False,
) -> ProcessingSummary:
    """Process raw runs not already completed."""
    configured_sources, selected_source_ids = _load_processing_config(
        config_path,
        selected_sources,
    )
    registry = build_parser_registry(project_root)
    summary = ProcessingSummary()
    if dry_run:
        return _run_dry_run(
            configured_sources, selected_source_ids, project_root, registry, summary
        )

    _run_database_processing(
        configured_sources,
        selected_source_ids,
        project_root,
        registry,
        summary,
        retry_partial,
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
    retry_partial: bool,
) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    with psycopg.connect(database_url) as connection:
        repository = ProcessingRepository(connection)
        for source_entry in _active_sources(configured_sources, selected_source_ids):
            context = _source_context(source_entry, project_root, registry)
            for run_directory in context.run_directories:
                summary.discovered += 1
                _process_run(
                    repository,
                    connection,
                    context,
                    run_directory,
                    project_root,
                    summary,
                    retry_partial,
                )


def _should_process_source(source_entry: dict[str, Any], selected_source_ids: set[str]) -> bool:
    source_id = source_entry["id"]
    return (not selected_source_ids or source_id in selected_source_ids) and source_entry.get(
        "enabled", True
    )


def _active_sources(
    configured_sources: list[dict[str, Any]],
    selected_source_ids: set[str],
) -> list[dict[str, Any]]:
    return [
        source_entry
        for source_entry in configured_sources
        if _should_process_source(source_entry, selected_source_ids)
    ]


def _source_context(
    source_entry: dict[str, Any],
    project_root: Path,
    registry: dict[str, RawRunParser],
) -> SourceContext:
    adapter_id = source_entry["id"]
    parser = registry.get(adapter_id)
    if parser is None:
        raise RuntimeError(f"No parser is registered for source: {adapter_id}")
    source_config = load_toml(resolve_project_path(project_root, source_entry["config_path"]))
    storage_directory = resolve_project_path(
        project_root,
        source_config["storage"]["directory"],
    )
    return SourceContext(
        adapter_id=adapter_id,
        parser=parser,
        run_directories=discover_raw_runs(storage_directory),
        source_config=source_config,
    )


def _run_dry_run(
    configured_sources: list[dict[str, Any]],
    selected_source_ids: set[str],
    project_root: Path,
    registry: dict[str, RawRunParser],
    summary: ProcessingSummary,
) -> ProcessingSummary:
    for source_entry in _active_sources(configured_sources, selected_source_ids):
        context = _source_context(source_entry, project_root, registry)
        for run_directory in context.run_directories:
            summary.discovered += 1
            print(f"[{context.adapter_id}] {run_directory}")
    return summary


def _process_run(
    repository: ProcessingRepository,
    connection: psycopg.Connection[Any],
    context: SourceContext,
    run_directory: Path,
    project_root: Path,
    summary: ProcessingSummary,
    retry_partial: bool,
) -> None:
    metadata = _load_metadata(run_directory / "metadata.json")
    run_id = _required_metadata_text(metadata, "run_id")
    metadata_source_id = _required_metadata_text(metadata, "source_id")
    source_key = _resolve_source_key(context, metadata, metadata_source_id)
    status = repository.register_raw_run(
        source_id=metadata_source_id,
        run_id=run_id,
        raw_path=run_directory.relative_to(project_root),
        retrieved_at=parse_datetime(metadata.get("retrieved_at")),
        record_count=_optional_int(metadata.get("record_count")),
        payload_sha256=optional_text(metadata.get("payload_sha256")),
    )
    connection.commit()
    if status == "processed" or (status == "partial" and not retry_partial):
        summary.skipped += 1
        return

    repository.mark_processing(metadata_source_id, run_id)
    connection.commit()
    try:
        result = context.parser.parse(run_directory / "response.json", metadata)
    except (OSError, TypeError, ValueError) as error:
        connection.rollback()
        repository.mark_failed(metadata_source_id, run_id, str(error))
        connection.commit()
        summary.failed += 1
        print(f"[{context.adapter_id}] failed {run_id}: {error}", file=sys.stderr)
        return

    retrieved_at = parse_datetime(metadata.get("retrieved_at")) or utc_now()
    _process_records(
        repository,
        connection,
        context.adapter_id,
        metadata_source_id,
        source_key,
        run_id,
        result,
        retrieved_at,
        _optional_int(metadata.get("record_count")),
        summary,
    )


def _process_records(
    repository: ProcessingRepository,
    connection: psycopg.Connection[Any],
    adapter_id: str,
    run_source_id: str,
    source_key: str,
    run_id: str,
    result: ParseResult,
    retrieved_at,
    expected_count: int | None,
    summary: ProcessingSummary,
) -> None:
    errors = list(result.errors)
    successful = 0
    for error in errors:
        _store_error(repository, connection, run_source_id, run_id, error)

    for record in result.records:
        try:
            with connection.transaction():
                repository.upsert_job_posting(record, source_key, retrieved_at, PARSER_VERSION)
        except (OSError, TypeError, ValueError, psycopg.Error) as error:
            record_error = RecordError(
                source_job_id=record.source_job_id,
                stage="database",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            errors.append(record_error)
            _store_error(repository, connection, run_source_id, run_id, record_error)
            continue
        successful += 1

    total = (
        expected_count if expected_count is not None else len(result.records) + len(result.errors)
    )
    if successful == 0:
        message = _error_summary(errors) or "No records were processed"
        with connection.transaction():
            repository.mark_failed(run_source_id, run_id, message)
        summary.failed += 1
        print(f"[{adapter_id}] failed {run_id}: {message}", file=sys.stderr)
        return

    if errors or successful < total:
        message = _error_summary(errors) or "Some records were not processed"
        with connection.transaction():
            repository.mark_partial(run_source_id, run_id, successful, PARSER_VERSION, message)
        summary.partial += 1
        summary.records += successful
        print(f"[{adapter_id}] partial {run_id}: {successful}/{total} records")
        return

    with connection.transaction():
        repository.mark_processed(run_source_id, run_id, successful, PARSER_VERSION)
        repository.mark_missing_postings_inactive(source_key, retrieved_at)
    summary.processed += 1
    summary.records += successful
    print(f"[{adapter_id}] processed {run_id}: {successful} records")


def _store_error(
    repository: ProcessingRepository,
    connection: psycopg.Connection[Any],
    source_id: str,
    run_id: str,
    error: RecordError,
) -> None:
    with connection.transaction():
        repository.record_error(source_id, run_id, error)


def _resolve_source_key(
    context: SourceContext,
    metadata: Mapping[str, Any],
    metadata_source_id: str,
) -> str:
    configured_keys = {
        str(board.get("source_key"))
        for board in context.source_config.get("boards", [])
        if board.get("source_key")
    }
    if metadata_source_id not in configured_keys | {context.adapter_id}:
        raise RuntimeError(
            f"Raw run source mismatch: adapter={context.adapter_id}, metadata={metadata_source_id}"
        )
    if metadata_source_id != context.adapter_id:
        return metadata_source_id
    metadata_context = metadata.get("context") or {}
    explicit_source_key = optional_text(metadata_context.get("source_key"))
    if explicit_source_key:
        return explicit_source_key
    company = optional_text(metadata_context.get("company"))
    for board in context.source_config.get("boards", []):
        if board.get("company") == company:
            return str(board.get("source_key", context.adapter_id))
    return context.adapter_id


def _error_summary(errors: list[RecordError]) -> str | None:
    if not errors:
        return None
    return "; ".join(error.error_message for error in errors[:3])


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
    parser.add_argument(
        "--retry-partial",
        action="store_true",
        help="Retry runs with status partial.",
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
            retry_partial=args.retry_partial,
        )
    except (OSError, RuntimeError, ValueError, psycopg.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(
        "Summary: "
        f"discovered={summary.discovered}, "
        f"processed={summary.processed}, "
        f"partial={summary.partial}, "
        f"skipped={summary.skipped}, "
        f"failed={summary.failed}, "
        f"records={summary.records}"
    )
    return 1 if summary.failed or summary.partial else 0


if __name__ == "__main__":
    raise SystemExit(main())
