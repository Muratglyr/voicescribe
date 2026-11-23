"""Sistemde ffmpeg'in kurulu olup olmadigini dogrulayan yardimci sinif."""

from __future__ import annotations

import shutil

from .exceptions import FFmpegNotFoundError


class FFmpegChecker:
    """Whisper'in ihtiyac duydugu ffmpeg bagimliligini dogrular."""

    @staticmethod
    def verify() -> None:
        """ffmpeg PATH icinde bulunamazsa anlasilir bir hata firlatir."""
        if shutil.which("ffmpeg") is None:
            raise FFmpegNotFoundError(
                "ffmpeg not found. Whisper needs ffmpeg to read audio files. "
                "See the 'Installation' section of README.md."
            )
