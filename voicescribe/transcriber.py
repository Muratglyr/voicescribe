"""OpenAI Whisper modelini yerel olarak calistirip ses dosyalarini metne cevirir."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import VALID_WHISPER_MODELS


@dataclass(frozen=True)
class TranscriptSegment:
    """Whisper'in urettigi, zaman damgali tek bir transkript parcasi."""

    start_seconds: float
    end_seconds: float
    text: str


class WhisperTranscriber:
    """Whisper modelini tembel (lazy) yukleyip ses dosyalarindan zaman damgali metin uretir.

    Model ve torch agir bagimliliklar oldugu icin ilk gercek kullanima kadar
    ice aktarilmaz; boylece bu sinif agir bagimliliklar kurulu olmadan da
    test edilebilir. Segment zaman damgalari, konusmaci ayrimi (diarization)
    sonuclariyla eslestirme yapabilmek icin saklanir.
    """

    def __init__(self, model_size: str, language: str) -> None:
        if model_size not in VALID_WHISPER_MODELS:
            raise ValueError(
                f"Invalid Whisper model size: '{model_size}'. "
                f"Valid values: {', '.join(VALID_WHISPER_MODELS)}"
            )
        self._model_size = model_size
        self._language = language
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        """Whisper modelini ilk erisimde yukler ve sonraki cagrilarda tekrar kullanir."""
        if self._model is None:
            import whisper

            self._model = whisper.load_model(self._model_size)
        return self._model

    def transcribe(self, audio_file: Path) -> list[TranscriptSegment]:
        """Verilen ses dosyasini tamamen yerel olarak, zaman damgali segmentlere ceviri.

        Internete hicbir veri gonderilmez.
        """
        result = self.model.transcribe(
            str(audio_file),
            language=self._language,
            verbose=False,
            # Onceki segmentin metnini bir sonraki segmentin decode baglamina
            # sokmaz; aksi halde bir segmentteki halisünasyon/bozuk metin
            # kendini besleyerek sonraki segmentlere de bulasip ayni ifadenin
            # sonsuz tekrarina ("bir de, bir de, bir de...") yol acabiliyor.
            condition_on_previous_text=False,
        )
        return [
            TranscriptSegment(
                start_seconds=segment["start"],
                end_seconds=segment["end"],
                text=segment["text"].strip(),
            )
            for segment in result["segments"]
        ]


def segments_to_text(segments: list[TranscriptSegment]) -> str:
    """Konusmaci ayrimi kullanilmadigi durumlarda segmentleri tek bir duz metne birlestirir."""
    return " ".join(segment.text for segment in segments)
