"""Project-wide normalization dictionaries loaded from TOML."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from job_market_intelligence.processing.aliases import AliasDictionary


@dataclass(frozen=True)
class NormalizationDictionaries:
    """All canonical-value dictionaries used by processing."""

    companies: AliasDictionary
    roles: AliasDictionary
    skills: AliasDictionary
    seniority_levels: AliasDictionary
    proficiency_levels: AliasDictionary
    requirement_types: AliasDictionary
    work_modes: AliasDictionary
    locations: AliasDictionary
    employment_relations: AliasDictionary
    workloads: AliasDictionary

    @classmethod
    def from_project_root(cls, project_root: Path) -> NormalizationDictionaries:
        """Load all normalization dictionaries from the project config."""
        directory = project_root / "config" / "normalization"
        return cls(
            companies=_load_dictionary(directory, "companies"),
            roles=_load_dictionary(directory, "roles"),
            skills=_load_dictionary(directory, "skills"),
            seniority_levels=_load_dictionary(directory, "seniority_levels"),
            proficiency_levels=_load_dictionary(directory, "proficiency_levels"),
            requirement_types=_load_dictionary(directory, "requirement_types"),
            work_modes=_load_dictionary(directory, "work_modes"),
            locations=_load_dictionary(directory, "locations"),
            employment_relations=_load_dictionary(directory, "employment_relations"),
            workloads=_load_dictionary(directory, "workloads"),
        )


def _load_dictionary(directory: Path, name: str) -> AliasDictionary:
    return AliasDictionary.from_file(directory / f"{name}.toml", name)
