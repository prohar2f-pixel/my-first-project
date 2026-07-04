"""Распознавание речи: Whisper через OpenRouter (OpenAI-совместимый API)."""
import os
import time
import logging
from io import BytesIO

from openai import OpenAI, RateLimitError

logger = logging.getLogger(__name__)

TG_LIMIT = 3500  # лимит Telegram 4096, берём с запасом на эмодзи и кавычки


def split_for_telegram(text: str, limit: int = TG_LIMIT) -> list[str]:
    """Режет текст на куски <= limit по границам слов (иначе — жёстко)."""
    text = text.strip()
    if not text:
        return []
    parts = []
    while len(text) > limit:
        cut = text.rfind(" ", 0, limit + 1)
        if cut <= limit // 2:  # нет пробела в разумных пределах — режем жёстко
            cut = limit
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    parts.append(text)
    return parts


class RateLimited(Exception):
    """API отдал 429 и после повтора — показать «подождите минуту»."""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
    return _client


def _call(client: OpenAI, data: bytes, filename: str) -> str:
    resp = client.audio.transcriptions.create(
        model="openai/whisper-1",  # OpenRouter проксирует OpenAI Whisper
        file=(filename, BytesIO(data)),  # имя с расширением обязательно — по нему API определяет формат
        language="ru",
        temperature=0,
    )
    return resp.text.strip()


def _retry_after_seconds(e: RateLimitError) -> float:
    try:
        return max(0.0, float(e.response.headers.get("retry-after", 5)))
    except (TypeError, ValueError, AttributeError):
        return 5.0


def transcribe(data: bytes, filename: str, client: OpenAI | None = None) -> str:
    """OGG/MP4 → текст. Один повтор с паузой; при повторном 429 — RateLimited."""
    client = client or _get_client()
    try:
        return _call(client, data, filename)
    except RateLimitError as e:
        wait = _retry_after_seconds(e)
        logger.warning(f"OpenRouter 429, повтор через {wait}с")
        time.sleep(wait)
        # ровно один повтор на вызов: не-429 ошибка второй попытки уходит наверх как есть
        try:
            return _call(client, data, filename)
        except RateLimitError:
            raise RateLimited() from None
    except Exception as e:
        logger.warning(f"OpenRouter error ({e!r}), повтор через 2с")
        time.sleep(2)
        return _call(client, data, filename)
