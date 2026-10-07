"""Shared configuration loading helpers for ingestion."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_toml(config_path: Path) -> dict[str, Any]:
    """Load a TOML configuration file."""
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)
