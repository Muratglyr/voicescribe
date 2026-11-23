"""Structured JSON output with speakers and timestamps, for further processing."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from voicescribe.core.domain import Transcript

FORMAT_NAME = "json"


class JsonWriter:
    def __init__(self, encoding: str, indent: int) -> None:
        self._encoding = encoding
        self._indent = indent

    @property
    def format_name(self) -> str:
        return FORMAT_NAME

    def supports(self, transcript: Transcript) -> bool:  # noqa: ARG002 - protocol signature
        return True

    def write(self, transcript: Transcript, target_without_suffix: Path) -> Path:
        path = target_without_suffix.with_name(f"{target_without_suffix.name}.{FORMAT_NAME}")
        document = json.dumps(asdict(transcript), ensure_ascii=False, indent=self._indent)
        path.write_text(document, encoding=self._encoding)
        return path
