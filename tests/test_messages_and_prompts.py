from __future__ import annotations

from pathlib import Path

import pytest

from voicescribe.config.messages import Messages
from voicescribe.config.prompts import PromptLibrary
from voicescribe.core.errors import ConfigurationError, InputError


def test_messages_are_formatted() -> None:
    assert Messages.load("en")("run.done", count=3) == "Done. 3 file(s) written."


def test_turkish_catalogue_is_used() -> None:
    assert Messages.load("tr")("run.done", count=1).startswith("Tamamlandi")


def test_unknown_locale_falls_back_to_english() -> None:
    assert Messages.load("xx")("run.done", count=0) == "Done. 0 file(s) written."


def test_error_renders_through_catalogue() -> None:
    error = InputError("error.path_not_found", path="a.wav")

    assert error.render(Messages.load("en")) == "Path not found: a.wav"


def test_packaged_prompt_is_rendered_with_variables() -> None:
    prompt = PromptLibrary().load("transcript_editor.md", speaker_a="S0", speaker_b="S1", separator=":")

    assert '"S0:"' in prompt
    assert "$speaker_a" not in prompt


def test_user_prompt_file_takes_precedence(tmp_path: Path) -> None:
    custom = tmp_path / "mine.md"
    custom.write_text("Hello $speaker_a", encoding="utf-8")

    assert PromptLibrary().load(str(custom), speaker_a="X") == "Hello X"


def test_missing_prompt_raises() -> None:
    with pytest.raises(ConfigurationError):
        PromptLibrary().load("does_not_exist.md")
