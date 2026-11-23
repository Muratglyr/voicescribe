"""Test doubles implementing the ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from voicescribe.domain import Transcript, Utterance


@dataclass
class FakeTranscriber:
    transcript: Transcript
    name: str = "fake"
    calls: list[Path] = field(default_factory=list)

    def transcribe(self, audio_file: Path) -> Transcript:
        self.calls.append(audio_file)
        return self.transcript


@dataclass
class UppercaseEditor:
    name: str = "upper"

    def edit(self, transcript: Transcript) -> Transcript:
        return Transcript.of((Utterance(u.text.upper(), u.speaker) for u in transcript.utterances), transcript.language)


class FakeChatClient:
    """Mimics ``openai.OpenAI().chat.completions.create``."""

    def __init__(self, reply: Any) -> None:
        self.requests: list[dict[str, Any]] = []
        self._reply = reply
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **request: Any) -> Any:
        self.requests.append(request)
        content = self._reply(request["messages"][-1]["content"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload
