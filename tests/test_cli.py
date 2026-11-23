from __future__ import annotations

from pathlib import Path

import pytest

from tests.fakes import FakeTranscriber
from voicescribe import cli
from voicescribe.adapters.audio import AudioSource
from voicescribe.adapters.writers import TextWriter
from voicescribe.application.pipeline import TranscriptionPipeline
from voicescribe.config.messages import Messages
from voicescribe.config.settings import Settings
from voicescribe.core.domain import Transcript
from voicescribe.core.errors import InputError
from voicescribe.core.formatting import TranscriptFormatter


def _overrides(settings: Settings, *argv: str) -> dict[str, object]:
    args = cli.build_parser(Messages.load("en"), settings).parse_args(list(argv))
    return cli.overrides_from(args, settings)


def test_flags_map_to_config_keys(settings: Settings) -> None:
    overrides = _overrides(
        settings, "a.m4a", "--language", "de", "--format", "srt", "--format", "json", "--edit", "--diarize", "--verbose"
    )

    assert overrides == {
        "transcription.language": "de",
        "output.formats": ["srt", "json"],
        "editing.enabled": True,
        "transcription.engine": settings.transcription.diarization_engine,
        "app.log_level": "DEBUG",
    }


def test_unset_flags_do_not_override_config(settings: Settings) -> None:
    assert _overrides(settings, "a.m4a") == {}


def test_main_reports_errors_and_returns_non_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main([str(tmp_path / "missing.wav"), "--diarize"]) == 1
    assert "Path not found" in caplog.text


def test_input_is_validated_before_system_checks(
    settings: Settings, formatter: TranscriptFormatter, messages: Messages, tmp_path: Path
) -> None:
    def ffmpeg_missing() -> None:
        raise AssertionError("preflight must not run before the input is validated")

    pipeline = TranscriptionPipeline(
        source=AudioSource(settings.audio),
        transcriber=FakeTranscriber(Transcript.of([])),
        writers=[TextWriter(formatter, "utf-8")],
        output=settings.output,
        messages=messages,
        preflight=[ffmpeg_missing],
    )

    with pytest.raises(InputError):
        pipeline.run(tmp_path / "missing.wav")
