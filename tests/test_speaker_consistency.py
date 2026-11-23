from voicescribe.speaker_consistency import find_speaker_consistency_warnings

RAW_TEXT = (
    "KONUSMACI_00: Sorry about that. Being part of a data science team was important to me "
    "and I really enjoyed working with my colleagues on interesting projects every day.\n\n"
    "KONUSMACI_01: I didn't understand your question, so what exactly do you want to know "
    "from us about the team structure and how we operate on a daily basis?\n\n"
    "KONUSMACI_00: One more question for me, are you using only classical machine learning "
    "processes, or are you also using generative AI tools in your daily workflow?\n\n"
    "KONUSMACI_01: We currently have a squad responsible for classical machine learning and "
    "data science products, and any type of analysis goes through that business squad.\n\n"
    "KONUSMACI_00: That's great to hear, thank you for explaining the team structure and how "
    "the different squads collaborate with each other on a daily basis.\n\n"
    "KONUSMACI_01: I want to thank you for your time today, we will follow up with the next "
    "steps of the process within the next few business days."
)


def test_no_warnings_when_labels_preserved_exactly() -> None:
    edited_text = RAW_TEXT  # degistirilmeden aynen korunmus

    warnings = find_speaker_consistency_warnings(RAW_TEXT, edited_text)

    assert warnings == []


def test_no_warnings_when_labels_consistently_renamed() -> None:
    edited_text = (
        "GUEST: Sorry about that. Being part of a data science team was important to me "
        "and I really enjoyed working with my colleagues on interesting projects every day.\n\n"
        "HOST: I didn't understand your question, so what exactly do you want to know "
        "from us about the team structure and how we operate on a daily basis?\n\n"
        "GUEST: One more question for me, are you using only classical machine learning "
        "processes, or are you also using generative AI tools in your daily workflow?\n\n"
        "HOST: We currently have a squad responsible for classical machine learning and "
        "data science products, and any type of analysis goes through that business squad.\n\n"
        "GUEST: That's great to hear, thank you for explaining the team structure and how "
        "the different squads collaborate with each other on a daily basis.\n\n"
        "HOST: I want to thank you for your time today, we will follow up with the next "
        "steps of the process within the next few business days."
    )

    warnings = find_speaker_consistency_warnings(RAW_TEXT, edited_text)

    assert warnings == []


def test_warns_when_a_turn_is_swapped_to_the_wrong_speaker() -> None:
    # Diger tum turler dogru etiketlenmisken, gercekte gozlemlenen hatayi
    # taklit ederek tek bir tur (konugun cumlesi) yanlislikla sunucuya
    # (KONUSMACI_01) atfedilmis.
    edited_text = (
        "KONUSMACI_01: Sorry about that. Being part of a data science team was important to me "
        "and I really enjoyed working with my colleagues on interesting projects every day.\n\n"
        "KONUSMACI_01: I didn't understand your question, so what exactly do you want to know "
        "from us about the team structure and how we operate on a daily basis?\n\n"
        "KONUSMACI_00: One more question for me, are you using only classical machine learning "
        "processes, or are you also using generative AI tools in your daily workflow?\n\n"
        "KONUSMACI_01: We currently have a squad responsible for classical machine learning and "
        "data science products, and any type of analysis goes through that business squad.\n\n"
        "KONUSMACI_00: That's great to hear, thank you for explaining the team structure and how "
        "the different squads collaborate with each other on a daily basis.\n\n"
        "KONUSMACI_01: I want to thank you for your time today, we will follow up with the next "
        "steps of the process within the next few business days."
    )

    warnings = find_speaker_consistency_warnings(RAW_TEXT, edited_text)

    assert len(warnings) == 1
    assert "Sorry about that" in warnings[0]
