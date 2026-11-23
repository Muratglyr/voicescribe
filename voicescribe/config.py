"""Uygulama genelinde kullanilan sabitler ve degismez ayar sinifi."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".m4a", ".mp3", ".wav", ".mp4", ".aac", ".ogg"})
VALID_WHISPER_MODELS: tuple[str, ...] = ("tiny", "base", "small", "medium", "large")

DEFAULT_WHISPER_MODEL = "medium"
DEFAULT_LANGUAGE = "en"
DEFAULT_OUTPUT_DIR = Path("./ciktilar")
EDITED_FILE_SUFFIX = "_duzenlenmis"

# LLM'e tek seferde gonderilecek metin parcasinin yaklasik ust siniri (karakter).
LLM_CHUNK_MAX_CHARS = 12000


@dataclass(frozen=True)
class AppConfig:
    """CLI argumanlarindan turetilen, tum calisma zamani ayarlarini tasiyan degismez veri sinifi.

    llm_model disaridan (CLI) verilmemisse None kalir; bu durumda
    OpenRouterSettings.model_name (OPENROUTER_MODEL ortam degiskeni)
    kullanilir. Kod icinde hicbir saglayici/model adi sabitlenmez.
    """

    input_path: Path
    folder_mode: bool
    whisper_model: str = DEFAULT_WHISPER_MODEL
    language: str = DEFAULT_LANGUAGE
    output_dir: Path = DEFAULT_OUTPUT_DIR
    edit: bool = False
    llm_model: str | None = None
    diarize: bool = False
