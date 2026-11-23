from __future__ import annotations

from voicescribe.domain import Transcript, Utterance
from voicescribe.formatting import TextChunker, TranscriptFormatter

SENTENCE_END = r"(?<=[.!?])\s+"


def test_merge_consecutive_speakers_keeps_timing() -> None:
    transcript = Transcript.of(
        [
            Utterance("Hi,", "A", 0.0, 1.0),
            Utterance("there.", "A", 1.0, 2.0),
            Utterance("Hello.", "B", 2.0, 3.0),
        ]
    )

    merged = transcript.merge_consecutive_speakers(" ")

    assert merged.utterances == (Utterance("Hi, there.", "A", 0.0, 2.0), Utterance("Hello.", "B", 2.0, 3.0))


def test_render_and_parse_round_trip(formatter: TranscriptFormatter) -> None:
    transcript = Transcript.of([Utterance("Hello.", "SPEAKER_00"), Utterance("Hi!", "SPEAKER_01")], "en")

    text = formatter.render(transcript)

    assert text == "SPEAKER_00: Hello.\n\nSPEAKER_01: Hi!"
    assert formatter.parse(text, "en") == transcript


def test_render_without_speakers_is_running_text(formatter: TranscriptFormatter) -> None:
    transcript = Transcript.of([Utterance("one"), Utterance("two")])

    assert formatter.render(transcript) == "one two"
    assert not transcript.is_diarized


def test_speaker_label_comes_from_config(formatter: TranscriptFormatter) -> None:
    assert formatter.speaker_label(3) == "SPEAKER_03"
    assert formatter.speaker_label(None) == "UNKNOWN_SPEAKER"


def test_chunker_keeps_turns_and_splits_oversized_ones_by_sentence() -> None:
    chunker = TextChunker(20, "\n\n", " ", SENTENCE_END)

    chunks = chunker.split("A: short.\n\nB: First long sentence. Second one.")

    assert chunks == ["A: short.", "B: First long sentence.", "Second one."]


def test_chunker_returns_single_chunk_for_short_text() -> None:
    chunker = TextChunker(100, "\n\n", " ", SENTENCE_END)

    assert chunker.split("A: hi.\n\nB: yo.") == ["A: hi.\n\nB: yo."]
