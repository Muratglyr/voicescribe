"""Copy-editing with any LLM behind an OpenAI-compatible chat completions API."""

from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from typing import Any

from voicescribe.adapters._optional import import_optional
from voicescribe.config.settings import LlmSettings
from voicescribe.core.domain import Transcript
from voicescribe.core.formatting import TextChunker, TranscriptFormatter

_PACKAGE = "openai"
_EXTRA = "llm"
_FEATURE = "editing"
_SYSTEM_ROLE = "system"
_USER_ROLE = "user"

ClientFactory = Callable[[str, str], Any]


def _openai_client(api_key: str, base_url: str) -> Any:
    return import_optional(_PACKAGE, extra=_EXTRA, feature=_FEATURE).OpenAI(api_key=api_key, base_url=base_url)


class LlmTranscriptEditor:
    """Renders the transcript to text, edits it chunk by chunk and parses the result back."""

    def __init__(
        self,
        *,
        settings: LlmSettings,
        api_key: str,
        system_prompt: str,
        formatter: TranscriptFormatter,
        chunker: TextChunker,
        client_factory: ClientFactory = _openai_client,
    ) -> None:
        self._settings = settings
        self._api_key = api_key
        self._system_prompt = system_prompt
        self._formatter = formatter
        self._chunker = chunker
        self._client_factory = client_factory

    @property
    def name(self) -> str:
        return self._settings.model

    @cached_property
    def _client(self) -> Any:
        return self._client_factory(self._api_key, self._settings.base_url)

    def edit(self, transcript: Transcript) -> Transcript:
        chunks = self._chunker.split(self._formatter.render(transcript))
        edited = self._formatter.turn_separator.join(self._complete(chunk) for chunk in chunks)
        return self._formatter.parse(edited, transcript.language)

    def _complete(self, chunk: str) -> str:
        response = self._client.chat.completions.create(
            model=self._settings.model,
            temperature=self._settings.temperature,
            messages=[
                {"role": _SYSTEM_ROLE, "content": self._system_prompt},
                {"role": _USER_ROLE, "content": chunk},
            ],
        )
        return str(response.choices[0].message.content).strip()
