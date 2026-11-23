"""Detects turns an editor moved to the wrong speaker.

LLMs edit long transcripts chunk by chunk and occasionally attribute a turn to the
other speaker. Each edited turn is paired with the most similar raw turn; for every
raw speaker the most common edited label is taken as the intended mapping, so a
consistent rename (``SPEAKER_00`` -> ``Guest``) is accepted and only deviations from
it are reported.
"""

from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher

from ..domain import Transcript, Utterance
from ..ports import SpeakerMixup
from ..settings import ConsistencySettings


class SpeakerConsistencyInspector:
    def __init__(self, settings: ConsistencySettings) -> None:
        self._settings = settings

    def inspect(self, raw: Transcript, edited: Transcript) -> list[SpeakerMixup]:
        raw_turns = [u for u in raw.utterances if u.speaker is not None]
        pairs = [
            (raw_speaker, turn)
            for turn in edited.utterances
            if turn.speaker is not None and len(turn.text) >= self._settings.min_content_length
            if (raw_speaker := self._best_match(turn, raw_turns)) is not None
        ]

        votes: dict[str, Counter[str]] = {}
        for raw_speaker, turn in pairs:
            votes.setdefault(raw_speaker, Counter())[str(turn.speaker)] += 1
        expected = {speaker: counter.most_common(1)[0][0] for speaker, counter in votes.items()}

        return [
            SpeakerMixup(
                snippet=turn.text[: self._settings.snippet_chars],
                raw_speaker=raw_speaker,
                edited_speaker=str(turn.speaker),
                expected_speaker=expected[raw_speaker],
            )
            for raw_speaker, turn in pairs
            if turn.speaker != expected[raw_speaker]
        ]

    def _best_match(self, turn: Utterance, candidates: list[Utterance]) -> str | None:
        limit = self._settings.compare_chars
        best_speaker, best_ratio = None, self._settings.min_match_ratio
        for candidate in candidates:
            ratio = SequenceMatcher(None, turn.text[:limit], candidate.text[:limit]).ratio()
            if ratio > best_ratio:
                best_speaker, best_ratio = candidate.speaker, ratio
        return best_speaker
