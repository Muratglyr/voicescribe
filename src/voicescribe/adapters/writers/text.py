"""Plain text output: ``LABEL: text`` turns, or running text without speakers."""

from __future__ import annotations

from pathlib import Path

from voicescribe.core.domain import Transcript
from voicescribe.core.formatting import TranscriptFormatter

FORMAT_NAME = "txt"


class TextWriter:
    def __init__(self, formatter: TranscriptFormatter, encoding: str) -> None:
        self._formatter = formatter
        self._encoding = encoding

    @property
    def format_name(self) -> str:
        return FORMAT_NAME

    def supports(self, transcript: Transcript) -> bool:  # noqa: ARG002 - protocol signature
        return True

    def write(self, transcript: Transcript, target_without_suffix: Path) -> Path:
        path = target_without_suffix.with_name(f"{target_without_suffix.name}.{FORMAT_NAME}")
        path.write_text(self._formatter.render(transcript), encoding=self._encoding)
        return path
