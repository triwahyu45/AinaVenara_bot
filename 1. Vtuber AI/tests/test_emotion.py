from aina_companion.emotion import emotion_prompt, parse_emotion


def test_parse_known_emotion():
    assert parse_emotion("[Senyum] Halo.", {"senyum", "biasa"}) == ("senyum", "Halo.")


def test_parse_unknown_emotion_falls_back():
    assert parse_emotion("[Lapar] Halo.", {"biasa"}) == ("biasa", "Halo.")


def test_prompt_lists_tags():
    assert "[Senyum]" in emotion_prompt({"senyum": "hotkey_senyum"})

