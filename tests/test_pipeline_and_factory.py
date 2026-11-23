from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from tests.fakes import FakeTranscriber, UppercaseEditor
from voicescribe.audio import AudioSource
from voicescribe.domain import Transcript, Utterance
from voicescribe.errors import ConfigurationError, InputError
from voicescribe.factory import PipelineFactory
from voicescribe.formatting import TranscriptFormatter
from voicescribe.messages import Messages
from voicescribe.pipeline import TranscriptionPipeline
from voicescribe.settings import Settings, SettingsLoader
from voicescribe.transcribers import DeepgramTranscriber, WhisperTranscriber
from voicescribe.writers import SrtWriter, TextWriter


def _audio(folder: Path, *names: str) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / name for name in names]
    for path in paths:
        path.write_bytes(b"")
    return paths


def test_pipeline_writes_raw_and_edited_and_skips_unsupported_formats(
    settings: Settings, formatter: TranscriptFormatter, messages: Messages, tmp_path: Path
) -> None:
    (audio,) = _audio(tmp_path / "in", "talk.m4a")
    pipeline = TranscriptionPipeline(
        source=AudioSource(settings.audio),
        transcriber=FakeTranscriber(Transcript.of([Utterance("hello", "SPEAKER_00")])),
        writers=[TextWriter(formatter, "utf-8"), SrtWriter(formatter, "utf-8")],
        output=settings.output,
        messages=messages,
        editor=UppercaseEditor(),
    )

    written = pipeline.run(audio)

    out = settings.output.directory
    assert written == [out / "talk.txt", out / "talk_edited.txt"]
    assert (out / "talk_edited.txt").read_text(encoding="utf-8") == "SPEAKER_00: HELLO"


def test_pipeline_runs_preflight_and_processes_folder_in_order(
    settings: Settings, formatter: TranscriptFormatter, messages: Messages, tmp_path: Path
) -> None:
    _audio(tmp_path / "in", "b.wav", "a.mp3", "notes.txt")
    checks: list[str] = []
    transcriber = FakeTranscriber(Transcript.of([Utterance("x")]))
    pipeline = TranscriptionPipeline(
        source=AudioSource(settings.audio),
        transcriber=transcriber,
        writers=[TextWriter(formatter, "utf-8")],
        output=settings.output,
        messages=messages,
        preflight=[lambda: checks.append("ok")],
    )

    pipeline.run(tmp_path / "in", folder_mode=True)

    assert checks == ["ok"]
    assert [p.name for p in transcriber.calls] == ["a.mp3", "b.wav"]


@pytest.mark.parametrize(
    ("name", "folder_mode", "key"),
    [
        ("missing.wav", False, "error.path_not_found"),
        ("doc.pdf", False, "error.unsupported_format"),
        ("doc.pdf", True, "error.not_a_folder"),
    ],
)
def test_audio_source_errors(settings: Settings, tmp_path: Path, name: str, folder_mode: bool, key: str) -> None:
    (tmp_path / "doc.pdf").write_bytes(b"")

    with pytest.raises(InputError) as error:
        AudioSource(settings.audio).discover(tmp_path / name, folder_mode)

    assert error.value.message_key == key


def test_ffmpeg_check_uses_configured_executable(settings: Settings) -> None:
    looked_up: list[str] = []

    def which(executable: str) -> None:
        looked_up.append(executable)

    with pytest.raises(InputError):
        AudioSource(settings.audio, which=which).verify_ffmpeg()
    assert looked_up == [settings.audio.ffmpeg_executable]


def _build(settings: Settings, messages: Messages, environ: dict[str, str]) -> TranscriptionPipeline:
    return PipelineFactory(settings, messages, environ=environ).build()


def _with_engine(settings: Settings, engine: str) -> Settings:
    return replace(settings, transcription=replace(settings.transcription, engine=engine))


def test_factory_selects_deepgram_when_key_present(settings: Settings, messages: Messages) -> None:
    pipeline = _build(_with_engine(settings, "deepgram"), messages, {"DEEPGRAM_API_KEY": "k"})

    assert isinstance(pipeline._transcriber, DeepgramTranscriber)


def test_factory_falls_back_to_whisper_without_key(settings: Settings, messages: Messages) -> None:
    pipeline = _build(_with_engine(settings, "deepgram"), messages, {})

    assert isinstance(pipeline._transcriber, WhisperTranscriber)


def test_factory_builds_editor_only_when_fully_configured(settings: Settings, messages: Messages) -> None:
    loader = SettingsLoader(environ={})
    enabled = {"editing.enabled": True, "editing.llm.model": "some/model"}
    key = {"OPENROUTER_API_KEY": "k"}

    assert _build(loader.load(overrides=enabled), messages, key)._editor is not None
    assert _build(loader.load(overrides=enabled), messages, {})._editor is None
    assert _build(loader.load(overrides={"editing.enabled": True}), messages, key)._editor is None


@pytest.mark.parametrize("overrides", [{"transcription.engine": "nope"}, {"output.formats": ["docx"]}])
def test_factory_rejects_unknown_plugins(settings: Settings, messages: Messages, overrides: dict[str, object]) -> None:
    with pytest.raises(ConfigurationError):
        _build(SettingsLoader(environ={}).load(overrides=overrides), messages, {})
