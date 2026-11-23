"""Speech-to-text engines implementing :class:`voicescribe.ports.Transcriber`."""

from .deepgram import DeepgramTranscriber
from .whisper import WhisperTranscriber

__all__ = ["DeepgramTranscriber", "WhisperTranscriber"]
