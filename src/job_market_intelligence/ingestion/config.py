"""Shared configuration loading helpers for ingestion."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_toml(config_path: Path) -> dict[str, Any]:
    """Load a TOML configuration file."""
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


def resolve_project_path(project_root: Path, path_value: str | Path) -> Path:
    """Resolve a project-relative path."""
    path = Path(path_value)
    return path if path.is_absolute() else project_root / path
