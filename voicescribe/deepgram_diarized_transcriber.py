"""Deepgram uzerinden ses dosyasini tek istekte hem transkript hem konusmaci
etiketleriyle birlikte metne cevirir.

Yerel pyannote.audio pipeline'inin yerini alir: transkripsiyon ve konusmaci
ayrimi ayni bulut istegiyle yapildigi icin, --konusmaci-ayir kullanildiginda
yerel Whisper adimina gerek kalmaz. Bu adimda ses dosyasi Deepgram'a
gonderilir (bkz. README "Veri Gizliligi").
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .provider_settings import DeepgramSettings

DEEPGRAM_LISTEN_URL = "https://api.deepgram.com/v1/listen"
UNKNOWN_SPEAKER_LABEL = "BILINMEYEN_KONUSMACI"


class DeepgramDiarizedTranscriber:
    """Deepgram'in /v1/listen ucuna ses dosyasi gonderip, donen konusmaci
    etiketli 'utterance'lari 'KONUSMACI_00: ...' formatinda birlestirir.
    """

    def __init__(self, language: str, settings: DeepgramSettings | None = None) -> None:
        self._language = language
        self._settings = settings if settings is not None else DeepgramSettings.from_env()

    def is_ready(self) -> bool:
        """API anahtari ve model adi (env'den) tanimli mi?"""
        return self._settings.is_complete()

    def transcribe(self, audio_file: Path) -> str:
        """Ses dosyasini Deepgram'a gonderip konusmaci etiketli metni dondurur."""
        import requests

        params = {
            "model": self._settings.model_name,
            "language": self._language,
            "diarize": "true",
            "punctuate": "true",
            "smart_format": "true",
            "utterances": "true",
        }
        with audio_file.open("rb") as file_obj:
            response = requests.post(
                DEEPGRAM_LISTEN_URL,
                params=params,
                headers={
                    "Authorization": f"Token {self._settings.api_key}",
                    "Content-Type": "audio/*",
                },
                data=file_obj,
                timeout=1800,
            )
        response.raise_for_status()
        utterances = response.json()["results"]["utterances"]
        return self._format_utterances(utterances)

    @staticmethod
    def _format_utterances(utterances: list[dict[str, Any]]) -> str:
        """Ardisik ayni-konusmacili utterance'lari tek satirda birlestirir."""
        lines: list[str] = []
        current_speaker: int | None = None
        current_parts: list[str] = []

        for utterance in utterances:
            speaker = utterance["speaker"]
            if speaker != current_speaker and current_parts:
                lines.append(f"{DeepgramDiarizedTranscriber._label(current_speaker)}: {' '.join(current_parts)}")
                current_parts = []
            current_parts.append(utterance["transcript"])
            current_speaker = speaker

        if current_parts:
            lines.append(f"{DeepgramDiarizedTranscriber._label(current_speaker)}: {' '.join(current_parts)}")

        return "\n\n".join(lines)

    @staticmethod
    def _label(speaker: int | None) -> str:
        return UNKNOWN_SPEAKER_LABEL if speaker is None else f"KONUSMACI_{speaker:02d}"
