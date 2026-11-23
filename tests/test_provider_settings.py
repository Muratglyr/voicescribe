import pytest

from voicescribe.provider_settings import DeepgramSettings, OpenRouterSettings


def test_openrouter_settings_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-5")

    settings = OpenRouterSettings.from_env()

    assert settings.is_complete() is True
    assert settings.model_name == "anthropic/claude-sonnet-5"


@pytest.mark.parametrize("missing_var", ["OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_MODEL"])
def test_openrouter_settings_incomplete_when_one_missing(monkeypatch: pytest.MonkeyPatch, missing_var: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-5")
    monkeypatch.delenv(missing_var, raising=False)

    settings = OpenRouterSettings.from_env()

    assert settings.is_complete() is False


def test_deepgram_settings_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    monkeypatch.setenv("DEEPGRAM_MODEL", "nova-3")

    settings = DeepgramSettings.from_env()

    assert settings.is_complete() is True


def test_deepgram_settings_incomplete_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    monkeypatch.delenv("DEEPGRAM_MODEL", raising=False)

    settings = DeepgramSettings.from_env()

    assert settings.is_complete() is False
