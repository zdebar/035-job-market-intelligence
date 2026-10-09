from decimal import Decimal
from pathlib import Path

from job_market_intelligence.processing.extraction import extract_hours
from job_market_intelligence.processing.sources.greenhouse import GreenhouseParser

PROJECT_ROOT = Path(__file__).parents[2]


def test_greenhouse_parser_extracts_normalized_values() -> None:
    parser = GreenhouseParser(PROJECT_ROOT)
    records = parser.parse_job(
        {
            "id": 123,
            "title": "Senior Data Engineer",
            "company_name": "Mews",
            "absolute_url": "https://example.test/job/123",
            "first_published": "2026-10-08T10:00:00+00:00",
            "updated_at": "2026-10-08T11:00:00+00:00",
            "location": {"name": "Prague, Czechia"},
            "metadata": [
                {"name": "Employment type", "value": "Employee - Permanent"},
                {"name": "Location type:", "value": ["Hybrid"]},
            ],
            "content": "Use Python, SQL and PostgreSQL. 20-30 hours per week.",
        },
        "Mews",
    )

    assert records.company_name == "Mews"
    assert records.role_name == "Data Engineer"
    assert records.seniority_level_name == "Senior"
    assert records.locations == ("Prague, Czechia",)
    assert records.work_modes == ("Hybrid",)
    assert records.employment_options[0].employment_relation_name == "Employee"
    assert records.employment_options[0].hours_min == Decimal("20")
    assert records.employment_options[0].hours_max == Decimal("30")
    assert records.employment_options[0].hours_period == "week"
    assert {skill.name for skill in records.skill_requirements} >= {
        "Python",
        "SQL",
        "PostgreSQL",
    }


def test_extract_hours_without_range() -> None:
    assert extract_hours("Work 20 hours weekly") == (
        Decimal("20"),
        Decimal("20"),
        "week",
    )
