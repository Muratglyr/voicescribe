"""Local transcription with OpenAI Whisper. Audio never leaves the machine."""

from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from pathlib import Path
from typing import Any

from .._optional import import_optional
from ..domain import Transcript, Utterance
from ..errors import ConfigurationError
from ..settings import WhisperSettings

ENGINE_NAME = "whisper"
_PACKAGE = "whisper"
_EXTRA = "whisper"

ModelLoader = Callable[[str], Any]


def _load_whisper_model(model: str) -> Any:
    return import_optional(_PACKAGE, extra=_EXTRA, feature=ENGINE_NAME).load_model(model)


class WhisperTranscriber:
    """Runs a Whisper model locally. The model is loaded lazily on first use."""

    def __init__(
        self,
        settings: WhisperSettings,
        language: str,
        model_loader: ModelLoader = _load_whisper_model,
    ) -> None:
        if settings.model not in settings.available_models:
            raise ConfigurationError(
                "error.invalid_model",
                model=settings.model,
                valid=", ".join(settings.available_models),
            )
        self._settings = settings
        self._language = language
        self._model_loader = model_loader

    @property
    def name(self) -> str:
        return f"{ENGINE_NAME} ({self._settings.model})"

    @cached_property
    def _model(self) -> Any:
        return self._model_loader(self._settings.model)

    def transcribe(self, audio_file: Path) -> Transcript:
        result = self._model.transcribe(
            str(audio_file),
            language=self._language,
            verbose=self._settings.verbose,
            condition_on_previous_text=self._settings.condition_on_previous_text,
        )
        return Transcript.of(
            (
                Utterance(text=segment["text"].strip(), start=segment["start"], end=segment["end"])
                for segment in result["segments"]
            ),
            self._language,
        )
