import asr


def test_split_empty_returns_nothing():
    assert asr.split_for_telegram("") == []
    assert asr.split_for_telegram("   ") == []


def test_split_short_text_single_chunk():
    assert asr.split_for_telegram("привет мир") == ["привет мир"]


def test_split_long_text_respects_limit_and_keeps_words():
    words = ["слово%d" % i for i in range(1200)]
    text = " ".join(words)  # ~10000 символов
    parts = asr.split_for_telegram(text, limit=3500)
    assert len(parts) >= 3
    assert all(len(p) <= 3500 for p in parts)
    # ни одно слово не потеряно и не разрезано
    assert " ".join(parts).split() == words


def test_split_text_without_spaces_hard_cut():
    text = "а" * 8000
    parts = asr.split_for_telegram(text, limit=3500)
    assert all(len(p) <= 3500 for p in parts)
    assert "".join(parts) == text
