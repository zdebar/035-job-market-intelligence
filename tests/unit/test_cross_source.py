import json
from pathlib import Path

from job_market_intelligence.ingestion.sources.ashby import build_endpoint as ashby_endpoint
from job_market_intelligence.ingestion.sources.ashby import load_toml as load_ashby
from job_market_intelligence.ingestion.sources.lever import build_endpoint as lever_endpoint
from job_market_intelligence.ingestion.sources.lever import load_toml as load_lever
from job_market_intelligence.processing.fingerprint import content_fingerprint
from job_market_intelligence.processing.sources.ashby import AshbyParser
from job_market_intelligence.processing.sources.lever import LeverParser

PROJECT_ROOT = Path(__file__).parents[2]


def test_fingerprint_ignores_html_entities_and_whitespace() -> None:
    assert content_fingerprint("<p>Python &amp; SQL</p>") == content_fingerprint(" Python & SQL ")


def test_lever_configuration_uses_board_source_key() -> None:
    config = load_lever(PROJECT_ROOT / "config" / "sources" / "lever.toml")

    assert config["boards"][0]["source_key"] == "lever_ataccama"
    assert lever_endpoint(config, "ataccama").endswith("/ataccama")


def test_ashby_configuration_uses_board_source_key() -> None:
    config = load_ashby(PROJECT_ROOT / "config" / "sources" / "ashby.toml")

    assert config["boards"][0]["source_key"] == "ashby_apify"
    assert ashby_endpoint(config, "apify").endswith("/apify")


def test_lever_parser_returns_normalized_record(tmp_path: Path) -> None:
    response_path = tmp_path / "lever.json"
    response_path.write_text(
        json.dumps(
            [
                {
                    "id": "lever-1",
                    "text": "Senior Data Engineer",
                    "hostedUrl": "https://jobs.example/lever-1",
                    "categories": {
                        "location": "Prague, Czechia",
                        "commitment": "Full-time",
                        "workplaceType": "Hybrid",
                    },
                    "descriptionPlain": "Build data pipelines with Python and SQL.",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = LeverParser(PROJECT_ROOT).parse(
        response_path,
        {"context": {"company": "Ataccama"}},
    )

    assert len(result.records) == 1
    assert not result.errors
    assert result.records[0].company_name == "Ataccama"
    assert result.records[0].role_name == "Data Engineer"
    assert result.records[0].locations == ("Prague, Czechia",)


def test_ashby_parser_returns_normalized_record(tmp_path: Path) -> None:
    response_path = tmp_path / "ashby.json"
    response_path.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "ashby-1",
                        "title": "AI Engineer",
                        "jobUrl": "https://jobs.example/ashby-1",
                        "location": "Remote",
                        "isRemote": True,
                        "employmentType": "Full-time",
                        "descriptionPlain": "Work with Python and machine learning.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = AshbyParser(PROJECT_ROOT).parse(
        response_path,
        {"context": {"company": "Apify"}},
    )

    assert len(result.records) == 1
    assert not result.errors
    assert result.records[0].company_name == "Apify"
    assert result.records[0].role_name == "AI Engineer"
    assert result.records[0].work_modes == ("Remote",)
