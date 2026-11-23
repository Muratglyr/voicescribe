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

# Eski Turkce bayraklar geriye donuk uyumluluk icin calismaya devam eder,
# ama --help ciktisinda gosterilmez.
_LEGACY_FLAG_ALIASES: dict[str, str] = {
    "--klasor": "--folder",
    "--dil": "--language",
    "--cikti": "--output",
    "--duzenle": "--edit",
    "--konusmaci-ayir": "--diarize",
}


def _translate_legacy_flags(argv: list[str]) -> list[str]:
    """Eski Turkce bayraklari Ingilizce karsiliklarina cevirir (orn. --dil=tr -> --language=tr)."""
    translated: list[str] = []
    for arg in argv:
        flag, sep, value = arg.partition("=")
        translated.append(f"{_LEGACY_FLAG_ALIASES[flag]}{sep}{value}" if flag in _LEGACY_FLAG_ALIASES else arg)
    return translated


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI argumanlarini tanimlar ve ayristirir."""
    parser = argparse.ArgumentParser(
        prog="voicescribe",
        description=(
            "Transcribe audio recordings locally with Whisper, optionally separate speakers "
            "with Deepgram, and optionally copy-edit the transcript with an LLM via OpenRouter."
        ),
    )
    parser.add_argument("input", type=Path, help="Audio file, or a folder when used with --folder")
    parser.add_argument(
        "--folder",
        dest="folder_mode",
        action="store_true",
        help="Treat the input as a folder and process every supported audio file in it",
    )
    parser.add_argument(
        "--model",
        dest="whisper_model",
        choices=VALID_WHISPER_MODELS,
        default=DEFAULT_WHISPER_MODEL,
        help=f"Whisper model size (default: {DEFAULT_WHISPER_MODEL})",
    )
    parser.add_argument(
        "--language",
        dest="language",
        default=DEFAULT_LANGUAGE,
        help=f"Language of the recording (default: {DEFAULT_LANGUAGE})",
    )
    parser.add_argument(
        "--output",
        dest="output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Folder to write transcripts to (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--edit",
        dest="edit",
        action="store_true",
        help=(
            "Copy-edit the raw transcript with an LLM via OpenRouter "
            "(needs OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL in .env)"
        ),
    )
    parser.add_argument(
        "--llm-model",
        dest="llm_model",
        default=None,
        help=(
            "OpenRouter model id for --edit (e.g. anthropic/claude-haiku-4.5). "
            "Defaults to the OPENROUTER_MODEL environment variable."
        ),
    )
    parser.add_argument(
        "--diarize",
        dest="diarize",
        action="store_true",
        help=(
            "Separate speakers with Deepgram. Transcription is then done by Deepgram "
            "instead of local Whisper (needs DEEPGRAM_API_KEY, DEEPGRAM_MODEL in .env)"
        ),
    )
    raw_argv = sys.argv[1:] if argv is None else argv
    return parser.parse_args(_translate_legacy_flags(raw_argv))


def build_config(args: argparse.Namespace) -> AppConfig:
    """argparse Namespace'ini degismez bir AppConfig'e cevirir."""
    return AppConfig(
        input_path=args.input,
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
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # kullaniciyi stack trace ile korkutmamak icin genel yakalama
        print(f"Unexpected error: {error}", file=sys.stderr)
        return 1

    print(f"\nDone. {len(created_files)} file(s) created.")
    return 0
