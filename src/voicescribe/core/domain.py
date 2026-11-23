"""Engine-independent transcript model shared by every component."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class Utterance:
    """A stretch of speech, optionally attributed to a speaker and placed in time."""

    text: str
    speaker: str | None = None
    start: float | None = None
    end: float | None = None

    @property
    def has_timing(self) -> bool:
        return self.start is not None and self.end is not None


@dataclass(frozen=True, slots=True)
class Transcript:
    """An ordered, immutable sequence of utterances."""

    utterances: tuple[Utterance, ...]
    language: str | None = None

    @classmethod
    def of(cls, utterances: Iterable[Utterance], language: str | None = None) -> Transcript:
        return cls(tuple(utterances), language)

    @property
    def is_diarized(self) -> bool:
        return any(utterance.speaker is not None for utterance in self.utterances)

    @property
    def has_timing(self) -> bool:
        return bool(self.utterances) and all(u.has_timing for u in self.utterances)

    def merge_consecutive_speakers(self, separator: str) -> Transcript:
        """Join neighbouring utterances of the same speaker into one turn."""
        merged: list[Utterance] = []
        for utterance in self.utterances:
            previous = merged[-1] if merged else None
            if previous is not None and previous.speaker == utterance.speaker:
                merged[-1] = replace(
                    previous,
                    text=separator.join((previous.text, utterance.text)),
                    end=utterance.end,
                )
            else:
                merged.append(utterance)
        return Transcript.of(merged, self.language)
