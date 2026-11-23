import pytest

from voicescribe.llm_editor import LlmEditor
from voicescribe.provider_settings import OpenRouterSettings


def test_not_ready_when_env_vars_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    editor = LlmEditor()

    assert editor.is_ready() is False


def test_ready_when_all_settings_present() -> None:
    settings = OpenRouterSettings(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model_name="anthropic/claude-sonnet-5",
    )

    editor = LlmEditor(settings=settings)

    assert editor.is_ready() is True
    assert editor.model_name == "anthropic/claude-sonnet-5"


def test_not_ready_when_api_key_missing_even_if_model_set() -> None:
    settings = OpenRouterSettings(api_key=None, base_url="https://openrouter.ai/api/v1", model_name="x/y")

    editor = LlmEditor(settings=settings)

    assert editor.is_ready() is False


def test_explicit_model_overrides_env_setting() -> None:
    settings = OpenRouterSettings(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model_name="openai/gpt-4o-mini",
    )

    editor = LlmEditor(model_name="anthropic/claude-sonnet-5", settings=settings)

    assert editor.model_name == "anthropic/claude-sonnet-5"


def test_falls_back_to_env_setting_when_model_not_given() -> None:
    settings = OpenRouterSettings(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model_name="openai/gpt-4o-mini",
    )

    editor = LlmEditor(model_name=None, settings=settings)

    assert editor.model_name == "openai/gpt-4o-mini"
