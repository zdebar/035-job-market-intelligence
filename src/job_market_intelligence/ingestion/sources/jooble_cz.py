"""Download one page of job listings from the Jooble CZ API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from job_market_intelligence.ingestion.http_client import HttpClient, HttpResponse

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources" / "jooble-cz.toml"


def load_config(config_path: Path) -> dict[str, Any]:
    """Load a source configuration from a TOML file."""
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


def build_payload(config: dict[str, Any], result_on_page: int | None = None) -> dict[str, Any]:
    """Build the Jooble request body from source configuration."""
    request_config = config["request"]
    payload: dict[str, Any] = {
        "keywords": request_config["keywords"],
        "location": request_config["location"],
        "page": request_config.get("page", 1),
        "ResultOnPage": request_config.get("result_on_page", 20),
        "companysearch": request_config.get("companysearch", False),
        "SearchMode": request_config.get("search_mode", 0),
    }

    configured_result_on_page = request_config.get("result_on_page")
    selected_result_on_page = (
        result_on_page if result_on_page is not None else configured_result_on_page
    )
    if selected_result_on_page is not None:
        payload["ResultOnPage"] = selected_result_on_page

    return payload


def get_api_key(config: dict[str, Any]) -> str:
    """Read the configured API key from the environment."""
    api_key_env = config["api"]["api_key_env"]
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing {api_key_env}. Add the Jooble API key to the local .env file.")
    return api_key


def build_endpoint(config: dict[str, Any], api_key: str) -> str:
    """Build the Jooble endpoint containing the API key."""
    base_url = config["api"]["base_url"].rstrip("/")
    return f"{base_url}/{api_key}"


def redact_endpoint(config: dict[str, Any]) -> str:
    """Return the endpoint without exposing the API key."""
    base_url = config["api"]["base_url"].rstrip("/")
    return f"{base_url}/<api-key>"


def save_raw_response(
    config: dict[str, Any],
    response: HttpResponse,
    payload: dict[str, Any],
) -> Path:
    """Save the original response body and non-secret metadata."""
    retrieved_at = datetime.now(UTC)
    run_id = uuid.uuid4().hex
    date_part = retrieved_at.strftime("%Y-%m-%d")
    relative_directory = Path(config["storage"]["directory"])
    output_directory = PROJECT_ROOT / relative_directory / date_part / run_id
    output_directory.mkdir(parents=True, exist_ok=False)

    response_path = output_directory / "response.json"
    metadata_path = output_directory / "metadata.json"
    response_path.write_bytes(response.content)

    metadata = {
        "source_id": config["source"]["id"],
        "retrieved_at": retrieved_at.isoformat(),
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "endpoint": redact_endpoint(config),
        "request": payload,
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return response_path


def download(config_path: Path, result_on_page: int | None = None) -> Path:
    """Download and store one Jooble response."""
    load_dotenv(PROJECT_ROOT / ".env")
    config = load_config(config_path)
    api_key = get_api_key(config)
    payload = build_payload(config, result_on_page=result_on_page)
    endpoint = build_endpoint(config, api_key)
    timeout = config["api"]["timeout_seconds"]

    try:
        response = HttpClient(timeout=timeout).post_json(endpoint, payload)
    except RuntimeError as error:
        raise RuntimeError(f"Jooble request failed: {error}") from error

    try:
        response.json()
    except json.JSONDecodeError as error:
        raise RuntimeError("Jooble returned a response that is not valid JSON.") from error

    return save_raw_response(config, response, payload)


def print_dry_run(config_path: Path, result_on_page: int | None = None) -> None:
    """Print the configured request without requiring a key or network access."""
    config = load_config(config_path)
    api_key_env = config["api"]["api_key_env"]
    key_status = "configured" if os.getenv(api_key_env) else "missing"
    print(f"Endpoint: {redact_endpoint(config)}")
    print(f"API key ({api_key_env}): {key_status}")
    print(
        json.dumps(
            build_payload(config, result_on_page=result_on_page),
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the source TOML configuration.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the request without using the API key or network.",
    )
    parser.add_argument(
        "--result-on-page",
        type=int,
        help="Temporarily limit the number of results returned by the request.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the Jooble downloader CLI."""
    args = parse_args()
    try:
        if args.dry_run:
            print_dry_run(args.config, result_on_page=args.result_on_page)
        else:
            response_path = download(args.config, result_on_page=args.result_on_page)
            print(f"Saved raw response to {response_path}")
    except (OSError, RuntimeError, tomllib.TOMLDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
