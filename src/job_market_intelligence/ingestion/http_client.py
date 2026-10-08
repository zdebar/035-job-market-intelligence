"""Reusable HTTP client helpers for ingestion sources."""

from __future__ import annotations

import json
import ssl
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
        self.ssl_context = ssl.create_default_context()
        self.headers = {"Accept": "application/json", **(headers or {})}

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_payload: Mapping[str, Any] | None = None,
    ) -> HttpResponse:
        """Send an HTTP request and return a transport-independent response."""
        try:
            with httpx.Client(
                timeout=self.timeout,
                headers=self.headers,
                verify=self.ssl_context,
            ) as client:
                response = client.request(
                    method,
                    url,
                    params=params,
                    json=json_payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise HttpRequestError(f"HTTP request failed: {error}") from error

        return HttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> HttpResponse:
        """Send a GET request."""
        return self.request("GET", url, params=params)

    def post_json(self, url: str, payload: Mapping[str, Any]) -> HttpResponse:
        """POST a JSON payload and return a transport-independent response."""
        return self.request("POST", url, json_payload=payload)
