"""Cloud transcription with speaker diarization via the Deepgram REST API.

The whole audio file is uploaded to Deepgram.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from voicescribe.adapters._optional import import_optional
from voicescribe.config.settings import DeepgramSettings
from voicescribe.core.domain import Transcript, Utterance

ENGINE_NAME = "deepgram"
_PACKAGE = "requests"
_EXTRA = "deepgram"

SpeakerLabeler = Callable[[int | None], str]
HttpPost = Callable[..., Any]


def _requests_post(*args: Any, **kwargs: Any) -> Any:
    return import_optional(_PACKAGE, extra=_EXTRA, feature=ENGINE_NAME).post(*args, **kwargs)


class DeepgramTranscriber:
    """Sends audio to Deepgram's ``/listen`` endpoint and maps utterances to a transcript."""

    def __init__(
        self,
        *,
        settings: DeepgramSettings,
        language: str,
        api_key: str,
        speaker_labeler: SpeakerLabeler,
        segment_separator: str,
        http_post: HttpPost = _requests_post,
    ) -> None:
        self._settings = settings
        self._language = language
        self._api_key = api_key
        self._label = speaker_labeler
        self._separator = segment_separator
        self._post = http_post

    @property
    def name(self) -> str:
        return f"{ENGINE_NAME} ({self._settings.model})"

    def transcribe(self, audio_file: Path) -> Transcript:
        with audio_file.open("rb") as audio:
            response = self._post(
                self._settings.api_url,
                params={"model": self._settings.model, "language": self._language, **self._settings.query},
                headers={
                    "Authorization": f"{self._settings.auth_scheme} {self._api_key}",
                    "Content-Type": self._settings.content_type,
                },
                data=audio,
                timeout=self._settings.timeout_seconds,
            )
        response.raise_for_status()
        return self.parse_response(response.json())

    def parse_response(self, payload: Mapping[str, Any]) -> Transcript:
        """Map a Deepgram JSON response (``results.utterances``) to a transcript."""
        utterances = (
            Utterance(
                text=item["transcript"],
                speaker=self._label(item.get("speaker")),
                start=item.get("start"),
                end=item.get("end"),
            )
            for item in payload["results"]["utterances"]
        )
        return Transcript.of(utterances, self._language).merge_consecutive_speakers(self._separator)
