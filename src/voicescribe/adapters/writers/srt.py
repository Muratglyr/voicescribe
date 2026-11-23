"""SubRip (``.srt``) subtitles. Requires timestamps on every utterance."""

from __future__ import annotations

from pathlib import Path

from voicescribe.core.domain import Transcript, Utterance
from voicescribe.core.formatting import TranscriptFormatter

FORMAT_NAME = "srt"
# Fixed by the SubRip specification.
_TIME_FORMAT = "{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
_TIME_RANGE = "{start} --> {end}"
_CUE_SEPARATOR = "\n\n"
_LINE_SEPARATOR = "\n"


class SrtWriter:
    def __init__(self, formatter: TranscriptFormatter, encoding: str) -> None:
        self._formatter = formatter
        self._encoding = encoding

    @property
    def format_name(self) -> str:
        return FORMAT_NAME

    def supports(self, transcript: Transcript) -> bool:
        return transcript.has_timing

    def write(self, transcript: Transcript, target_without_suffix: Path) -> Path:
        path = target_without_suffix.with_name(f"{target_without_suffix.name}.{FORMAT_NAME}")
        cues = (self._cue(index, utterance) for index, utterance in enumerate(transcript.utterances, start=1))
        path.write_text(_CUE_SEPARATOR.join(cues) + _LINE_SEPARATOR, encoding=self._encoding)
        return path

    def _cue(self, index: int, utterance: Utterance) -> str:
        assert utterance.start is not None
        assert utterance.end is not None
        text = utterance.text
        if utterance.speaker is not None:
            text = f"{utterance.speaker}{self._formatter.speaker_separator}{text}"
        time_range = _TIME_RANGE.format(start=_timestamp(utterance.start), end=_timestamp(utterance.end))
        return _LINE_SEPARATOR.join((str(index), time_range, text))


def _timestamp(seconds: float) -> str:
    total_millis = round(seconds * 1000)
    hours, rest = divmod(total_millis, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return _TIME_FORMAT.format(hours=hours, minutes=minutes, seconds=secs, millis=millis)
