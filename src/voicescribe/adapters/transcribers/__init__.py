"""Speech-to-text engines implementing :class:`voicescribe.ports.Transcriber`."""

from voicescribe.adapters.transcribers.deepgram import DeepgramTranscriber
from voicescribe.adapters.transcribers.whisper import WhisperTranscriber

__all__ = ["DeepgramTranscriber", "WhisperTranscriber"]
