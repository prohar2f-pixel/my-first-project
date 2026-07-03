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


from types import SimpleNamespace

import httpx
import pytest
from openai import RateLimitError


def _rate_limit_error(retry_after: str = "0"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions")
    resp = httpx.Response(429, headers={"retry-after": retry_after}, request=req)
    return RateLimitError("rate limited", response=resp, body=None)


class FakeClient:
    """audio.transcriptions.create: отдаёт по очереди элементы results —
    строки возвращает как .text, исключения бросает."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = 0
        self.audio = SimpleNamespace(
            transcriptions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls += 1
        r = self._results.pop(0)
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(text=r)


@pytest.fixture
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(asr.time, "sleep", sleeps.append)
    return sleeps


def test_transcribe_success_first_try(no_sleep):
    client = FakeClient(["  привет  "])
    assert asr.transcribe(b"ogg", "voice.ogg", client=client) == "привет"
    assert client.calls == 1
    assert no_sleep == []


def test_transcribe_retries_on_429_with_retry_after(no_sleep):
    client = FakeClient([_rate_limit_error("7"), "текст"])
    assert asr.transcribe(b"ogg", "voice.ogg", client=client) == "текст"
    assert client.calls == 2
    assert no_sleep == [7.0]


def test_transcribe_two_429_raises_ratelimited(no_sleep):
    client = FakeClient([_rate_limit_error(), _rate_limit_error()])
    with pytest.raises(asr.RateLimited):
        asr.transcribe(b"ogg", "voice.ogg", client=client)


def test_transcribe_retries_once_on_network_error(no_sleep):
    client = FakeClient([ConnectionError("boom"), "ок"])
    assert asr.transcribe(b"ogg", "voice.ogg", client=client) == "ок"
    assert no_sleep == [2]


def test_transcribe_network_error_twice_propagates(no_sleep):
    client = FakeClient([ConnectionError("boom"), ConnectionError("boom")])
    with pytest.raises(ConnectionError):
        asr.transcribe(b"ogg", "voice.ogg", client=client)
