from __future__ import annotations

from pathlib import Path

import pytest

from voicescribe import cli
from voicescribe.messages import Messages
from voicescribe.settings import Settings


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
