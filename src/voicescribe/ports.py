"""Interfaces the pipeline depends on. Concrete adapters live in sub-packages.

Adding a new speech engine, editor or output format means writing a class that
satisfies one of these protocols and registering it in :mod:`voicescribe.factory`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .domain import Transcript


class Transcriber(Protocol):
    """Turns an audio file into a transcript."""

    @property
    def name(self) -> str: ...

    def transcribe(self, audio_file: Path) -> Transcript: ...


class TranscriptEditor(Protocol):
    """Returns an improved version of a transcript (e.g. punctuation fixed)."""

    @property
    def name(self) -> str: ...

    def edit(self, transcript: Transcript) -> Transcript: ...


class TranscriptWriter(Protocol):
    """Serialises a transcript to a file."""

    @property
    def format_name(self) -> str: ...

    def supports(self, transcript: Transcript) -> bool: ...

    def write(self, transcript: Transcript, target_without_suffix: Path) -> Path: ...


@dataclass(frozen=True, slots=True)
class SpeakerMixup:
    """A turn whose speaker label changed inconsistently during editing."""

    snippet: str
    raw_speaker: str
    edited_speaker: str
    expected_speaker: str


class TranscriptInspector(Protocol):
    """Compares a raw and an edited transcript and reports suspicious changes."""

    def inspect(self, raw: Transcript, edited: Transcript) -> list[SpeakerMixup]: ...
