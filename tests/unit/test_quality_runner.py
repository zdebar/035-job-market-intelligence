from pathlib import Path

from job_market_intelligence.quality.runner import discover_quality_checks


def test_quality_checks_are_discovered_in_sorted_order(tmp_path: Path) -> None:
    quality_directory = tmp_path / "quality"
    quality_directory.mkdir()
    (quality_directory / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (quality_directory / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (quality_directory / "README.md").write_text("documentation", encoding="utf-8")

    assert discover_quality_checks(quality_directory) == [
        quality_directory / "001_first.sql",
        quality_directory / "002_second.sql",
    ]
