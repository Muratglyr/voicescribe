from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from tests.fakes import FakeChatClient, FakeResponse
from voicescribe.domain import Transcript, Utterance
from voicescribe.editors import LlmTranscriptEditor, SpeakerConsistencyInspector
from voicescribe.errors import ConfigurationError
from voicescribe.formatting import TextChunker, TranscriptFormatter
from voicescribe.settings import Settings
from voicescribe.transcribers import DeepgramTranscriber, WhisperTranscriber
from voicescribe.writers import JsonWriter, SrtWriter, TextWriter

DEEPGRAM_PAYLOAD = {
    "results": {
        "utterances": [
            {"speaker": 0, "transcript": "Hello,", "start": 0.0, "end": 0.5},
            {"speaker": 0, "transcript": "how are you?", "start": 0.5, "end": 1.2},
            {"speaker": 1, "transcript": "Fine, thanks.", "start": 1.4, "end": 2.0},
        ]
    }
}


class FakeWhisperModel:
    def __init__(self) -> None:
        self.options: dict[str, Any] = {}

    def transcribe(self, path: str, **options: Any) -> dict[str, Any]:
        self.options = options
        return {"segments": [{"text": " one ", "start": 0.0, "end": 1.0}, {"text": "two", "start": 1.0, "end": 2.5}]}


def test_whisper_maps_segments_and_passes_config(settings: Settings) -> None:
    model = FakeWhisperModel()
    transcriber = WhisperTranscriber(settings.transcription.whisper, "en", model_loader=lambda _: model)

    transcript = transcriber.transcribe(Path("a.wav"))

    assert transcript.utterances[0] == Utterance("one", None, 0.0, 1.0)
    assert model.options["condition_on_previous_text"] is settings.transcription.whisper.condition_on_previous_text


def test_whisper_rejects_unknown_model(settings: Settings) -> None:
    with pytest.raises(ConfigurationError):
        WhisperTranscriber(replace(settings.transcription.whisper, model="gigantic"), "en")


def test_deepgram_request_and_response_mapping(
    settings: Settings, formatter: TranscriptFormatter, tmp_path: Path
) -> None:
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    seen: dict[str, Any] = {}

    def post(url: str, **kwargs: Any) -> FakeResponse:
        seen.update(url=url, **kwargs)
        return FakeResponse(DEEPGRAM_PAYLOAD)

    transcriber = DeepgramTranscriber(
        settings=settings.transcription.deepgram,
        language="en",
        api_key="secret",
        speaker_labeler=formatter.speaker_label,
        segment_separator=" ",
        http_post=post,
    )

    transcript = transcriber.transcribe(audio)

    assert seen["url"] == settings.transcription.deepgram.api_url
    assert seen["headers"]["Authorization"] == "Token secret"
    assert seen["params"]["diarize"] == "true"
    assert transcript.utterances == (
        Utterance("Hello, how are you?", "SPEAKER_00", 0.0, 1.2),
        Utterance("Fine, thanks.", "SPEAKER_01", 1.4, 2.0),
    )


def test_llm_editor_sends_prompt_and_parses_reply(settings: Settings, formatter: TranscriptFormatter) -> None:
    client = FakeChatClient(reply=lambda text: text.replace("hello", "Hello."))
    editor = LlmTranscriptEditor(
        settings=settings.editing.llm,
        api_key="key",
        system_prompt="SYSTEM",
        formatter=formatter,
        chunker=TextChunker.from_settings(settings.editing.llm.chunk_max_chars, settings.format),
        client_factory=lambda key, url: client,
    )
    raw = Transcript.of([Utterance("hello", "SPEAKER_00"), Utterance("hi", "SPEAKER_01")], "en")

    edited = editor.edit(raw)

    assert edited.utterances[0] == Utterance("Hello.", "SPEAKER_00")
    assert client.requests[0]["messages"][0] == {"role": "system", "content": "SYSTEM"}
    assert client.requests[0]["temperature"] == settings.editing.llm.temperature


def _dialogue(*speakers: str) -> Transcript:
    lines = [
        "Being part of a data science team was important to me and I enjoyed it.",
        "What exactly do you want to know about the team structure and our days?",
        "Are you using only classical machine learning or also generative tools?",
        "We have a squad responsible for classical machine learning products.",
    ]
    return Transcript.of(Utterance(text, speaker) for text, speaker in zip(lines, speakers, strict=True))


def test_inspector_accepts_consistent_rename(settings: Settings) -> None:
    raw = _dialogue("S0", "S1", "S0", "S1")
    edited = _dialogue("Guest", "Host", "Guest", "Host")

    assert SpeakerConsistencyInspector(settings.consistency).inspect(raw, edited) == []


def test_inspector_flags_swapped_turn(settings: Settings) -> None:
    raw = _dialogue("S0", "S1", "S0", "S1")
    edited = _dialogue("S0", "S1", "S0", "S0")

    issues = SpeakerConsistencyInspector(settings.consistency).inspect(raw, edited)

    assert [(i.raw_speaker, i.edited_speaker, i.expected_speaker) for i in issues] == [("S1", "S0", "S1")]


def test_writers_produce_expected_files(formatter: TranscriptFormatter, tmp_path: Path) -> None:
    transcript = Transcript.of([Utterance("Hi.", "A", 0.0, 1.5), Utterance("Hey.", "B", 61.0, 62.25)], "en")
    target = tmp_path / "talk"

    txt = TextWriter(formatter, "utf-8").write(transcript, target)
    data = json.loads(JsonWriter("utf-8", 2).write(transcript, target).read_text(encoding="utf-8"))
    srt = SrtWriter(formatter, "utf-8").write(transcript, target).read_text(encoding="utf-8")

    assert txt.read_text(encoding="utf-8") == "A: Hi.\n\nB: Hey."
    assert data["utterances"][1] == {"text": "Hey.", "speaker": "B", "start": 61.0, "end": 62.25}
    assert "2\n00:01:01,000 --> 00:01:02,250\nB: Hey." in srt


def test_srt_requires_timestamps(formatter: TranscriptFormatter) -> None:
    assert not SrtWriter(formatter, "utf-8").supports(Transcript.of([Utterance("no timing")]))
