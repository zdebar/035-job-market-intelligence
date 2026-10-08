from pathlib import Path

from job_market_intelligence.ingestion.config import load_toml
from job_market_intelligence.ingestion.runner import run_ingestion

CONFIG_PATH = Path("config/ingestion.toml")


def test_ingestion_configuration_lists_greenhouse() -> None:
    config = load_toml(CONFIG_PATH)

    assert config["settings"]["path"] == "config/settings.toml"
    assert config["sources"] == [
        {
            "id": "greenhouse",
            "enabled": True,
            "config_path": "config/sources/greenhouse.toml",
        }
    ]


def test_runner_dry_run_does_not_need_api_key(capsys) -> None:
    saved_paths = run_ingestion(CONFIG_PATH, dry_run=True)

    assert saved_paths == []
    assert "Source: greenhouse" in capsys.readouterr().out
