"""Uzun metinleri LLM baglam sinirina uygun parcalara bolen yardimci sinif."""

from __future__ import annotations

import re


class TextChunker:
    """Metni, cumle sinirlarini bozmadan belirli bir karakter sinirinin altindaki parcalara boler."""

    _SENTENCE_END_PATTERN = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_chars: int) -> None:
        self._max_chars = max_chars

    def split(self, text: str) -> list[str]:
        """Metni max_chars sinirini asmayan, cumle butunlugunu koruyan parcalara ayirir."""
        if len(text) <= self._max_chars:
            return [text]

        sentences = self._SENTENCE_END_PATTERN.split(text)
        chunks: list[str] = []
        current_chunk = ""

        for sentence in sentences:
            candidate = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
            if len(candidate) > self._max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk = candidate

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
