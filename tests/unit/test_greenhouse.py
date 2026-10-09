from pathlib import Path

from job_market_intelligence.ingestion.sources.greenhouse import (
    build_endpoint,
    build_params,
    enabled_boards,
    load_config,
)

CONFIG_PATH = Path("config/sources/greenhouse.toml")


def test_greenhouse_configuration_loads() -> None:
    config = load_config(CONFIG_PATH)

    assert config["source"]["id"] == "greenhouse"
    assert config["api"]["base_url"] == "https://boards-api.greenhouse.io/v1/boards"


def test_greenhouse_boards_are_configured() -> None:
    config = load_config(CONFIG_PATH)

    assert len(enabled_boards(config)) == 2
    assert enabled_boards(config)[0]["board_token"] == "mewssystems"


def test_greenhouse_endpoint_and_parameters() -> None:
    config = load_config(CONFIG_PATH)

    assert build_endpoint(config, "mewssystems") == (
        "https://boards-api.greenhouse.io/v1/boards/mewssystems/jobs"
    )
    assert build_params(config) == {"content": "true"}
