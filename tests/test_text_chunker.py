from voicescribe.text_chunker import TextChunker


def test_short_text_returns_single_chunk() -> None:
    chunker = TextChunker(max_chars=100)

    result = chunker.split("Kisa bir cumle.")

    assert result == ["Kisa bir cumle."]


def test_long_text_splits_on_sentence_boundaries() -> None:
    chunker = TextChunker(max_chars=20)
    text = "Birinci cumle burada. Ikinci cumle burada. Ucuncu cumle burada."

    result = chunker.split(text)

    assert len(result) == 3
    assert " ".join(result) == text


def test_chunks_stay_within_limit_in_normal_case() -> None:
    chunker = TextChunker(max_chars=50)
    text = "Bu cumle kisa. Bu da kisa. Ucuncusu de oyle. Dorduncusu burada."

    result = chunker.split(text)

    assert all(len(chunk) <= 50 for chunk in result)
