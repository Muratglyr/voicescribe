from __future__ import annotations

from pathlib import Path

import pytest

from voicescribe.config.settings import SettingsLoader
from voicescribe.core.errors import ConfigurationError


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_defaults_are_loaded_from_packaged_toml() -> None:
    settings = SettingsLoader(environ={}).load()

    assert settings.transcription.engine == "whisper"
    assert settings.output.directory == Path("transcripts")
    assert settings.output.formats == ("txt",)


def test_layers_override_in_order(tmp_path: Path) -> None:
    config = tmp_path / "custom.toml"
    config.write_text('[transcription]\nlanguage = "de"\n[output]\njson_indent = 4\n', encoding="utf-8")
    environ = {"VOICESCRIBE__TRANSCRIPTION__LANGUAGE": "fr", "VOICESCRIBE__CONSISTENCY__ENABLED": "false"}

    settings = SettingsLoader(environ).load(config, overrides={"output.formats": ["srt", "json"]})

    assert settings.transcription.language == "fr"  # env beats file
    assert settings.output.json_indent == 4  # file beats defaults
    assert settings.consistency.enabled is False  # env strings are coerced
    assert settings.output.formats == ("srt", "json")  # overrides beat everything


def test_user_config_file_is_picked_up_automatically(tmp_path: Path) -> None:
    (tmp_path / "voicescribe.toml").write_text('[app]\nlocale = "tr"\n', encoding="utf-8")

    assert SettingsLoader(environ={}).load().app.locale == "tr"


def test_missing_explicit_config_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        SettingsLoader(environ={}).load(tmp_path / "nope.toml")


def test_unknown_keys_are_rejected(tmp_path: Path) -> None:
    config = tmp_path / "typo.toml"
    config.write_text("[output]\nformat = ['txt']\n", encoding="utf-8")

    with pytest.raises(ConfigurationError) as error:
        SettingsLoader(environ={}).load(config)

    assert error.value.message_key == "error.unknown_config_keys"
