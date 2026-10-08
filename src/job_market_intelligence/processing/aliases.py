"""Alias dictionaries used by deterministic normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from job_market_intelligence.ingestion.config import load_toml


@dataclass(frozen=True)
class AliasRule:
    """One canonical value and its source-text aliases."""

    canonical_name: str
    aliases: tuple[str, ...]


class AliasDictionary:
    """Find canonical values in source text using word-aware matching."""

    def __init__(self, rules: tuple[AliasRule, ...]) -> None:
        self._patterns = tuple(
            (
                rule.canonical_name,
                re.compile(
                    rf"(?<!\w){re.escape(alias)}(?!\w)",
                    flags=re.IGNORECASE,
                ),
            )
            for rule in rules
            for alias in sorted(rule.aliases, key=len, reverse=True)
            if alias
        )

    @classmethod
    def from_file(cls, path: Path, section: str) -> AliasDictionary:
        """Load one alias dictionary from a TOML file."""
        config = load_toml(path)
        values = config.get(section)
        if not isinstance(values, list):
            raise ValueError(f"Expected TOML array '{section}' in {path}")

        rules = tuple(
            AliasRule(
                canonical_name=str(item["name"]),
                aliases=tuple(str(alias) for alias in item.get("aliases", [])),
            )
            for item in values
        )
        return cls(rules)

    def find_all(self, text: str) -> tuple[str, ...]:
        """Return unique canonical values found in source order."""
        matches: list[tuple[int, str]] = []
        for canonical_name, pattern in self._patterns:
            match = pattern.search(text)
            if match:
                matches.append((match.start(), canonical_name))

        matches.sort(key=lambda item: (item[0], item[1]))
        return tuple(dict.fromkeys(canonical_name for _, canonical_name in matches))

    def find_non_overlapping(self, text: str) -> tuple[str, ...]:
        """Return matches while preferring the longest overlapping alias."""
        matches: list[tuple[int, int, str]] = []
        for canonical_name, pattern in self._patterns:
            match = pattern.search(text)
            if match:
                matches.append((match.start(), match.end(), canonical_name))

        matches.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[2]))
        selected: list[tuple[int, int, str]] = []
        for match in matches:
            if any(match[0] < selected_match[1] for selected_match in selected):
                continue
            selected.append(match)

        selected.sort(key=lambda item: item[0])
        return tuple(dict.fromkeys(canonical_name for _, _, canonical_name in selected))

    def find_first(self, text: str) -> str | None:
        """Return the first matching canonical value."""
        matches: list[tuple[int, int, str]] = []
        for canonical_name, pattern in self._patterns:
            match = pattern.search(text)
            if match:
                matches.append((match.start(), -len(match.group(0)), canonical_name))

        if not matches:
            return None
        matches.sort()
        return matches[0][2]
