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
                "ffmpeg bulunamadi. Whisper ses dosyalarini isleyebilmek icin ffmpeg gerektirir. "
                "Kurulum talimatlari icin README.md dosyasindaki 'Kurulum' bolumune bakin."
            )
