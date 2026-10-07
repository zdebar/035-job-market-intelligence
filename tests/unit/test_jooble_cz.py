from pathlib import Path

from job_market_intelligence.ingestion.sources.jooble_cz import (
    build_payload,
    load_config,
    redact_endpoint,
)

CONFIG_PATH = Path("config/sources/jooble-cz.toml")
SETTINGS_PATH = Path("config/settings.toml")


def test_jooble_configuration_loads() -> None:
    config = load_config(CONFIG_PATH)

    assert config["source"]["id"] == "jooble-cz"
    assert config["api"]["api_key_env"] == "JOOBLE_API_KEY"


def test_jooble_payload_uses_configured_values() -> None:
    config = load_config(CONFIG_PATH)
    settings = load_config(SETTINGS_PATH)

    assert build_payload(config, settings) == {
        "keywords": "Data Engineer, AI Engineer",
        "location": "Czech Republic",
        "page": 1,
        "companysearch": False,
        "SearchMode": 0,
    }


def test_jooble_payload_can_be_limited_for_testing() -> None:
    config = load_config(CONFIG_PATH)
    settings = load_config(SETTINGS_PATH)

    assert build_payload(config, settings, result_on_page=10)["ResultOnPage"] == 10


def test_endpoint_redaction_does_not_contain_api_key() -> None:
    config = load_config(CONFIG_PATH)

    assert redact_endpoint(config) == "https://cz.jooble.org/api/<api-key>"
