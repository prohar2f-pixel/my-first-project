"""Распознавание речи: Whisper large-v3 через Groq (OpenAI-совместимый API)."""
import os
import time
import logging
from io import BytesIO

from openai import OpenAI, RateLimitError

logger = logging.getLogger(__name__)

ASR_MODEL = os.environ.get("ASR_MODEL", "whisper-large-v3")

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
