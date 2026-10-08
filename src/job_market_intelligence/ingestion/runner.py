"""Run all enabled data-acquisition source adapters."""

from __future__ import annotations

import argparse
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

from job_market_intelligence.ingestion.config import load_toml, resolve_project_path
from job_market_intelligence.ingestion.sources import greenhouse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "ingestion.toml"

DownloadHandler = Callable[[Path, Path], list[Path]]
DryRunHandler = Callable[[Path, Path], None]

SOURCE_HANDLERS: dict[str, tuple[DownloadHandler, DryRunHandler]] = {
    "greenhouse": (greenhouse.download, greenhouse.print_dry_run),
}


def run_ingestion(
    config_path: Path,
    selected_sources: list[str] | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Run enabled configured sources and return saved response paths."""
    runner_config = load_toml(config_path)
    settings_path = resolve_project_path(
        PROJECT_ROOT,
        runner_config.get("settings", {}).get("path", "config/settings.toml")
    )
    configured_sources = runner_config.get("sources", [])
    selected_source_ids = set(selected_sources or [])
    configured_source_ids = {entry["id"] for entry in configured_sources}

    unknown_selected_sources = selected_source_ids - configured_source_ids
    if unknown_selected_sources:
        unknown = ", ".join(sorted(unknown_selected_sources))
        raise RuntimeError(f"Source is not present in ingestion configuration: {unknown}")

    saved_paths: list[Path] = []
    for source_entry in configured_sources:
        source_id = source_entry["id"]
        if selected_source_ids and source_id not in selected_source_ids:
            continue
        if not source_entry.get("enabled", True):
            print(f"Skipped disabled source: {source_id}")
            continue

        handlers = SOURCE_HANDLERS.get(source_id)
        if handlers is None:
            raise RuntimeError(f"No adapter is registered for source: {source_id}")

        source_config_path = resolve_project_path(PROJECT_ROOT, source_entry["config_path"])
        download_handler, dry_run_handler = handlers
        if dry_run:
            print(f"Source: {source_id}")
            dry_run_handler(source_config_path, settings_path)
        else:
            response_paths = download_handler(source_config_path, settings_path)
            saved_paths.extend(response_paths)
            for response_path in response_paths:
                print(f"[{source_id}] Saved raw response to {response_path}")

    return saved_paths


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the ingestion runner TOML configuration.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="selected_sources",
        help="Run only this configured source; may be provided more than once.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configured requests without using API keys or network access.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the configured ingestion sources."""
    args = parse_args()
    try:
        run_ingestion(
            args.config,
            selected_sources=args.selected_sources,
            dry_run=args.dry_run,
        )
    except (KeyError, OSError, RuntimeError, tomllib.TOMLDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
