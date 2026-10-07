"""Reusable HTTP client helpers for ingestion sources."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx


class HttpRequestError(RuntimeError):
    """Raised when an HTTP request cannot be completed successfully."""


@dataclass(frozen=True)
class HttpResponse:
    """Transport-independent representation of an HTTP response."""

    status_code: int
    headers: Mapping[str, str]
    content: bytes

    def json(self) -> Any:
        """Decode the response body as JSON."""
        return json.loads(self.content)


class HttpClient:
    """Small reusable HTTP client for source adapters."""

    def __init__(self, timeout: float, headers: Mapping[str, str] | None = None) -> None:
        self.timeout = timeout
        self.headers = {"Accept": "application/json", **(headers or {})}

    def post_json(self, url: str, payload: Mapping[str, Any]) -> HttpResponse:
        """POST a JSON payload and return a transport-independent response."""
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise HttpRequestError(f"HTTP request failed: {error}") from error

        return HttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )
