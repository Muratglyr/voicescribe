"""Komut satiri arayuzu: argumanlari ayristirir ve TranscriptPipeline'i calistirir."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WHISPER_MODEL,
    VALID_WHISPER_MODELS,
    AppConfig,
)
from .exceptions import TranscriptError
from .pipeline import TranscriptPipeline

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv opsiyoneldir; .env o zaman elle export edilmelidir
    load_dotenv = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI argumanlarini tanimlar ve ayristirir."""
    parser = argparse.ArgumentParser(
        prog="transkript.py",
        description=(
            "Ses kayitlarini yerel olarak (Whisper) metne cevirir, istege bagli "
            "olarak konusmacilari Deepgram ile ayirt eder ve OpenRouter uzerinden bir "
            "LLM ile duzenler."
        ),
    )
    parser.add_argument("girdi", type=Path, help="Ses dosyasi ya da (--klasor ile) klasor yolu")
    parser.add_argument(
        "--klasor",
        dest="folder_mode",
        action="store_true",
        help="Girdi bir klasordur; icindeki tum desteklenen ses dosyalari toplu islenir",
    )
    parser.add_argument(
        "--model",
        dest="whisper_model",
        choices=VALID_WHISPER_MODELS,
        default=DEFAULT_WHISPER_MODEL,
        help=f"Whisper model boyutu (varsayilan: {DEFAULT_WHISPER_MODEL})",
    )
    parser.add_argument(
        "--dil",
        dest="language",
        default=DEFAULT_LANGUAGE,
        help=f"Transkript dili (varsayilan: {DEFAULT_LANGUAGE})",
    )
    parser.add_argument(
        "--cikti",
        dest="output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Ciktilarin yazilacagi klasor (varsayilan: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--duzenle",
        dest="edit",
        action="store_true",
        help=(
            "Ham transkripti OpenRouter uzerinden bir LLM ile duzenle "
            "(OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL .env'de tanimli olmali)"
        ),
    )
    parser.add_argument(
        "--llm-model",
        dest="llm_model",
        default=None,
        help=(
            "--duzenle icin kullanilacak OpenRouter model adi (ornek: anthropic/claude-sonnet-5). "
            "Verilmezse OPENROUTER_MODEL ortam degiskeni kullanilir."
        ),
    )
    parser.add_argument(
        "--konusmaci-ayir",
        dest="diarize",
        action="store_true",
        help=(
            "Ses dosyasindaki farkli konusmacilari Deepgram ile ayirt et; bu durumda "
            "transkripsiyon da yerel Whisper yerine Deepgram uzerinden yapilir "
            "(DEEPGRAM_API_KEY, DEEPGRAM_MODEL .env'de tanimli olmali)"
        ),
    )
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> AppConfig:
    """argparse Namespace'ini degismez bir AppConfig'e cevirir."""
    return AppConfig(
        input_path=args.girdi,
        folder_mode=args.folder_mode,
        whisper_model=args.whisper_model,
        language=args.language,
        output_dir=args.output_dir,
        edit=args.edit,
        llm_model=args.llm_model,
        diarize=args.diarize,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI giris noktasi. Cikis kodu dondurur (0: basari, 1: hata)."""
    if load_dotenv is not None:
        load_dotenv()  # .env dosyasindaki degiskenleri (varsa) ortam degiskenlerine yukler

    args = parse_args(argv)
    config = build_config(args)

    try:
        pipeline = TranscriptPipeline(config)
        created_files = pipeline.run()
    except TranscriptError as error:
        print(f"HATA: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # kullaniciyi stack trace ile korkutmamak icin genel yakalama
        print(f"Beklenmeyen bir hata olustu: {error}", file=sys.stderr)
        return 1

    print(f"\nTamamlandi. {len(created_files)} dosya olusturuldu.")
    return 0
