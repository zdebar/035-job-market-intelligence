"""Generic raw-response storage for ingestion sources."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from job_market_intelligence.ingestion.http_client import HttpResponse


def save_raw_response(
    *,
    project_root: Path,
    storage_directory: str | Path,
    source_id: str,
    method: str,
    endpoint: str,
    response: HttpResponse,
    request: Mapping[str, Any],
    record_count: int | None = None,
    extra_metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Save the original response body and non-secret metadata."""
    retrieved_at = datetime.now(UTC)
    run_id = uuid.uuid4().hex
    date_part = retrieved_at.strftime("%Y-%m-%d")
    relative_directory = Path(storage_directory)
    base_directory = (
        relative_directory
        if relative_directory.is_absolute()
        else project_root / relative_directory
    )
    output_directory = base_directory / date_part / run_id
    output_directory.mkdir(parents=True, exist_ok=False)

    response_path = output_directory / "response.json"
    metadata_path = output_directory / "metadata.json"
    response_path.write_bytes(response.content)

    metadata: dict[str, Any] = {
        "run_id": run_id,
        "source_id": source_id,
        "retrieved_at": retrieved_at.isoformat(),
        "http_method": method,
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "endpoint": endpoint,
        "request": dict(request),
        "payload_sha256": hashlib.sha256(response.content).hexdigest(),
        "payload_size_bytes": len(response.content),
        "record_count": record_count,
    }
    if extra_metadata:
        metadata["context"] = dict(extra_metadata)

    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return response_path
