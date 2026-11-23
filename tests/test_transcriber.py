import pytest

from voicescribe.transcriber import WhisperTranscriber


def test_invalid_model_size_raises_error() -> None:
    with pytest.raises(ValueError):
        WhisperTranscriber(model_size="dev-boyut", language="tr")


def test_valid_model_size_is_accepted() -> None:
    # Whisper modeli sadece .model erisiminde (lazy) yuklenir, bu yuzden
    # bu test agir bagimliliklar (torch, whisper) kurulu olmasa da calisir.
    transcriber = WhisperTranscriber(model_size="small", language="tr")

    assert transcriber is not None
