from voicescribe.deepgram_diarized_transcriber import DeepgramDiarizedTranscriber


def test_consecutive_same_speaker_utterances_are_merged() -> None:
    utterances = [
        {"speaker": 0, "transcript": "Merhaba,"},
        {"speaker": 0, "transcript": "nasilsiniz?"},
        {"speaker": 1, "transcript": "Iyiyim tesekkurler."},
        {"speaker": 0, "transcript": "Kendinizden bahseder misiniz?"},
    ]

    result = DeepgramDiarizedTranscriber._format_utterances(utterances)

    assert result.split("\n\n") == [
        "SPEAKER_00: Merhaba, nasilsiniz?",
        "SPEAKER_01: Iyiyim tesekkurler.",
        "SPEAKER_00: Kendinizden bahseder misiniz?",
    ]


def test_single_speaker_produces_single_line() -> None:
    utterances = [
        {"speaker": 0, "transcript": "Birinci cumle."},
        {"speaker": 0, "transcript": "Ikinci cumle."},
    ]

    result = DeepgramDiarizedTranscriber._format_utterances(utterances)

    assert result == "SPEAKER_00: Birinci cumle. Ikinci cumle."


def test_empty_utterances_produce_empty_string() -> None:
    assert DeepgramDiarizedTranscriber._format_utterances([]) == ""
