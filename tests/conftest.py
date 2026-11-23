from __future__ import annotations

from pathlib import Path

import pytest

from voicescribe.formatting import TranscriptFormatter
from voicescribe.messages import Messages
from voicescribe.settings import Settings, SettingsLoader


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.chdir(tmp_path)  # isolate from any ./voicescribe.toml
    return SettingsLoader(environ={}).load(overrides={"output.directory": str(tmp_path / "out")})


@pytest.fixture
def messages() -> Messages:
    return Messages.load("en")


@pytest.fixture
def formatter(settings: Settings) -> TranscriptFormatter:
    return TranscriptFormatter(settings.format)
