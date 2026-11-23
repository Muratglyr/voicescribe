"""Proje icin ozel hata siniflari."""

from __future__ import annotations


class TranscriptError(Exception):
    """Tum proje-ozel hatalarin turedigi temel sinif."""


class FFmpegNotFoundError(TranscriptError):
    """Sistemde ffmpeg kurulu degilse firlatilir."""


class InputNotFoundError(TranscriptError):
    """Girdi olarak verilen dosya ya da klasor bulunamadiginda ya da gecersizse firlatilir."""


class UnsupportedFileError(TranscriptError):
    """Desteklenmeyen bir ses dosyasi formati verildiginde firlatilir."""
