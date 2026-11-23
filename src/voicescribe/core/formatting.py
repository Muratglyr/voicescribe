"""Conversion between :class:`Transcript` and its plain-text representation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from voicescribe.core.domain import Transcript, Utterance


@dataclass(frozen=True)
class FormatSettings:
    speaker_label: str
    unknown_speaker_label: str
    speaker_separator: str
    turn_separator: str
    segment_separator: str
    sentence_end_pattern: str
    turn_pattern: str


class TranscriptFormatter:
    """Renders transcripts as ``LABEL: text`` turns and parses them back."""

    def __init__(self, settings: FormatSettings) -> None:
        self._settings = settings
        self._turn_pattern = re.compile(settings.turn_pattern, re.DOTALL)

    @property
    def turn_separator(self) -> str:
        return self._settings.turn_separator

    @property
    def segment_separator(self) -> str:
        return self._settings.segment_separator

    @property
    def speaker_separator(self) -> str:
        return self._settings.speaker_separator

    def speaker_label(self, index: int | None) -> str:
        if index is None:
            return self._settings.unknown_speaker_label
        return self._settings.speaker_label.format(index=index)

    def render(self, transcript: Transcript) -> str:
        if not transcript.is_diarized:
            return self._settings.segment_separator.join(u.text for u in transcript.utterances)
        return self._settings.turn_separator.join(
            f"{u.speaker or self._settings.unknown_speaker_label}{self._settings.speaker_separator}{u.text}"
            for u in transcript.utterances
        )

    def parse(self, text: str, language: str | None = None) -> Transcript:
        utterances = []
        for block in filter(None, (b.strip() for b in text.split(self._settings.turn_separator))):
            match = self._turn_pattern.match(block)
            if match:
                utterances.append(Utterance(text=match.group(2).strip(), speaker=match.group(1).strip()))
            else:
                utterances.append(Utterance(text=block))
        return Transcript.of(utterances, language)


class TextChunker:
    """Splits text into chunks below a size limit without breaking turns or sentences."""

    def __init__(
        self,
        max_chars: int,
        block_separator: str,
        sentence_separator: str,
        sentence_end_pattern: str,
    ) -> None:
        self._max_chars = max_chars
        self._block_separator = block_separator
        self._sentence_separator = sentence_separator
        self._sentence_end = re.compile(sentence_end_pattern)

    @classmethod
    def from_settings(cls, max_chars: int, settings: FormatSettings) -> TextChunker:
        return cls(
            max_chars,
            settings.turn_separator,
            settings.segment_separator,
            settings.sentence_end_pattern,
        )

    def split(self, text: str) -> list[str]:
        chunks: list[str] = []
        current = ""
        for piece, joiner in self._pieces(text):
            candidate = f"{current}{joiner}{piece}" if current else piece
            if current and len(candidate) > self._max_chars:
                chunks.append(current)
                current = piece
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

    def _pieces(self, text: str) -> list[tuple[str, str]]:
        """Blocks that fit as they are; oversized blocks broken into sentences."""
        pieces: list[tuple[str, str]] = []
        for block in text.split(self._block_separator):
            if len(block) <= self._max_chars:
                pieces.append((block, self._block_separator))
                continue
            sentences = self._sentence_end.split(block)
            pieces.append((sentences[0], self._block_separator))
            pieces.extend((sentence, self._sentence_separator) for sentence in sentences[1:])
        return pieces
