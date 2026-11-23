"""Ses dosyalarini transkripte cevirme ve istege bagli konusmaci ayrimi / LLM duzenleme
surecini yoneten orkestratordur.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .config import AppConfig, EDITED_FILE_SUFFIX
from .deepgram_diarized_transcriber import DeepgramDiarizedTranscriber
from .ffmpeg_checker import FFmpegChecker
from .file_finder import AudioFileFinder
from .llm_editor import LlmEditor
from .speaker_consistency import find_speaker_consistency_warnings
from .transcriber import WhisperTranscriber, segments_to_text

try:
    from tqdm import tqdm
except ImportError:  # tqdm opsiyoneldir; kurulu degilse duz listeyle devam edilir
    tqdm = None

# torch (Whisper'in bagimliligi), islevi etkilemeyen ic loglar basabiliyor
# (orn. triton bulunamadi uyarisi); bunlari susturuyoruz ki terminalde asil
# ilerleme mesajlari gorulebilsin.
logging.getLogger("torch").setLevel(logging.ERROR)


class TranscriptPipeline:
    """Dosya bulma, transkripsiyon, konusmaci ayrimi ve LLM duzenleme adimlarini
    bir araya getiren ana is akisi.
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._file_finder = AudioFileFinder()
        self._transcriber = WhisperTranscriber(config.whisper_model, config.language)
        self._editor = LlmEditor(config.llm_model) if config.edit else None
        self._diarized_transcriber = (
            DeepgramDiarizedTranscriber(config.language) if config.diarize else None
        )

    def run(self) -> list[Path]:
        """Tum sureci calistirir ve olusturulan dosyalarin listesini dondurur."""
        FFmpegChecker.verify()
        audio_files = self._file_finder.find_files(self._config.input_path, self._config.folder_mode)
        self._config.output_dir.mkdir(parents=True, exist_ok=True)
        self._validate_editor()
        self._validate_diarizer()

        created_files: list[Path] = []
        total = len(audio_files)
        iterator = tqdm(audio_files, desc="Ses dosyalari", unit="dosya") if tqdm else audio_files

        for index, audio_file in enumerate(iterator, start=1):
            print(f"[{index}/{total}] Isleniyor: {audio_file.name}")
            created_files.extend(self._process_file(audio_file))

        return created_files

    def _validate_editor(self) -> None:
        """Gerekli OpenRouter ayarlari eksikse duzenleme adimini sessizce devre disi birakir."""
        if self._editor is not None and not self._editor.is_ready():
            print(
                "UYARI: OPENROUTER_API_KEY / OPENROUTER_BASE_URL / OPENROUTER_MODEL "
                "(veya --llm-model) eksik. --duzenle adimi atlanacak, sadece ham transkript "
                "olusturulacak."
            )
            self._editor = None
        elif self._editor is not None:
            print(f"LLM duzenleme modeli (OpenRouter): {self._editor.model_name}")

    def _validate_diarizer(self) -> None:
        """Gerekli Deepgram ayarlari eksikse konusmaci ayrimi adimini sessizce devre disi birakir."""
        if self._diarized_transcriber is not None and not self._diarized_transcriber.is_ready():
            print(
                "UYARI: DEEPGRAM_API_KEY / DEEPGRAM_MODEL eksik. --konusmaci-ayir adimi "
                "atlanacak, transkript yerel Whisper ile ve konusmaci etiketi olmadan uretilecek."
            )
            self._diarized_transcriber = None

    def _process_file(self, audio_file: Path) -> list[Path]:
        results: list[Path] = []

        if self._diarized_transcriber is not None:
            print("  Deepgram ile transkript + konusmaci ayrimi yapiliyor...")
            raw_text = self._diarized_transcriber.transcribe(audio_file)
        else:
            segments = self._transcriber.transcribe(audio_file)
            raw_text = segments_to_text(segments)

        raw_file_path = self._config.output_dir / f"{audio_file.stem}.txt"
        raw_file_path.write_text(raw_text, encoding="utf-8")
        results.append(raw_file_path)
        print(f"  Ham transkript kaydedildi: {raw_file_path}")

        if self._editor is not None:
            print("  LLM ile duzenleniyor...")
            edited_text = self._editor.edit(raw_text)
            for warning in find_speaker_consistency_warnings(raw_text, edited_text):
                print(f"  UYARI: {warning}")
            edited_file_path = self._config.output_dir / f"{audio_file.stem}{EDITED_FILE_SUFFIX}.txt"
            edited_file_path.write_text(edited_text, encoding="utf-8")
            results.append(edited_file_path)
            print(f"  Duzenlenmis transkript kaydedildi: {edited_file_path}")

        return results
