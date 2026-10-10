"""Stable fingerprints for matching equivalent job descriptions."""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def normalized_content(text: str) -> str:
    """Return HTML-free, whitespace-normalized, casefolded text."""
    parser = _TextExtractor()
    parser.feed(text)
    parser.close()
    plain_text = " ".join(parser.parts)
    return re.sub(r"\s+", " ", plain_text).strip().casefold()


def content_fingerprint(text: str) -> str:
    """Return the SHA-256 fingerprint of normalized advertisement content."""
    return hashlib.sha256(normalized_content(text).encode("utf-8")).hexdigest()
