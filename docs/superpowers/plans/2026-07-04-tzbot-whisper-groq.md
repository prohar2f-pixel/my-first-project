# План: Whisper large-v3 (Groq) в ТЗ-боте + видеокружочки

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить распознавание голосовых с Google Web Speech на Whisper large-v3 через Groq API и научить бота распознавать видеокружочки.

**Architecture:** Логика распознавания выносится в новый модуль `tzbot/asr.py` (ленивый Groq-клиент, ретраи, нарезка текста под лимит Telegram) — он тестируется pytest'ом без env-переменных и сети. `main.py` остаётся обвязкой: хендлеры скачивают файл из Telegram и зовут `asr.transcribe` через `asyncio.to_thread`. Зависимости `SpeechRecognition`/`pydub`/`ffmpeg` удаляются — Groq принимает OGG и MP4 напрямую.

**Tech Stack:** Python 3.11, python-telegram-bot 21.x, openai SDK (Groq — OpenAI-совместимый API), pytest (только локально, в деплой не идёт).

**Спека:** `docs/superpowers/specs/2026-07-04-tzbot-whisper-large-v3-design.md`

**Прекондиция для деплоя (не для тестов):** ключ с https://console.groq.com → API Keys. Задачи 1–5 выполняются без ключа.

---

## Структура файлов

- Create: `tzbot/asr.py` — распознавание: Groq-клиент, `transcribe()` с ретраями, `split_for_telegram()`
- Create: `tzbot/test_asr.py` — тесты чистой логики (без сети и env)
- Modify: `tzbot/main.py` — `handle_voice`, новый `handle_video_note`, общий помощник, регистрация, подсказка
- Modify: `tzbot/requirements.txt`, `tzbot/nixpacks.toml`, `tzbot/.env.example`

Рабочая директория: команды `python`/`pytest` выполняются из
`C:\Users\Udacha\Documents\projects\my-first-project\tzbot`, команды `git` — из
корня репозитория `my-first-project` (пути в `git add` даны от корня).
Локально один раз: `pip install pytest openai` (openai уже в requirements, pytest — только локально).

---

### Task 1: `asr.split_for_telegram` — нарезка текста под лимит Telegram

**Files:**
- Create: `tzbot/asr.py`
- Test: `tzbot/test_asr.py`

- [ ] **Step 1: Написать падающий тест**

Создать `tzbot/test_asr.py`:

```python
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
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `python -m pytest test_asr.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'asr'`

- [ ] **Step 3: Минимальная реализация**

Создать `tzbot/asr.py`:

```python
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
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

Run: `python -m pytest test_asr.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tzbot/asr.py tzbot/test_asr.py
git commit -m "feat(tzbot): asr.split_for_telegram — нарезка транскрипта под лимит Telegram"
```

---

### Task 2: `asr.transcribe` — Groq Whisper с ретраями

**Files:**
- Modify: `tzbot/asr.py` (дописать в конец)
- Test: `tzbot/test_asr.py` (дописать в конец)

- [ ] **Step 1: Написать падающие тесты**

Дописать в `tzbot/test_asr.py`:

```python
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
```

- [ ] **Step 2: Запустить — убедиться, что новые тесты падают**

Run: `python -m pytest test_asr.py -v`
Expected: первые 4 passed, новые 5 FAIL — `AttributeError: module 'asr' has no attribute 'transcribe'` (и `RateLimited`)

- [ ] **Step 3: Реализация**

Дописать в `tzbot/asr.py`:

```python
class RateLimited(Exception):
    """Groq отдал 429 и после повтора — показать «подождите минуту»."""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ["GROQ_API_KEY"],
        )
    return _client


def _call(client: OpenAI, data: bytes, filename: str) -> str:
    resp = client.audio.transcriptions.create(
        model=ASR_MODEL,
        file=(filename, BytesIO(data)),  # имя с расширением обязательно — по нему API определяет формат
        language="ru",
        temperature=0,
    )
    return resp.text.strip()


def _retry_after_seconds(e: RateLimitError) -> float:
    try:
        return float(e.response.headers.get("retry-after", 5))
    except (TypeError, ValueError, AttributeError):
        return 5.0


def transcribe(data: bytes, filename: str, client: OpenAI | None = None) -> str:
    """OGG/MP4 → текст. Один повтор с паузой; при повторном 429 — RateLimited."""
    client = client or _get_client()
    try:
        return _call(client, data, filename)
    except RateLimitError as e:
        wait = _retry_after_seconds(e)
        logger.warning(f"Groq 429, повтор через {wait}с")
        time.sleep(wait)
        try:
            return _call(client, data, filename)
        except RateLimitError:
            raise RateLimited() from None
    except Exception as e:
        logger.warning(f"Groq error ({e!r}), повтор через 2с")
        time.sleep(2)
        return _call(client, data, filename)
```

- [ ] **Step 4: Запустить тесты — все проходят**

Run: `python -m pytest test_asr.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add tzbot/asr.py tzbot/test_asr.py
git commit -m "feat(tzbot): asr.transcribe — Groq Whisper large-v3 с ретраями (429 по retry-after, сеть/5xx через 2с)"
```

---

### Task 3: `handle_voice` на новый движок + показ без Markdown кусками + лимит 10 минут

**Files:**
- Modify: `tzbot/main.py:1070-1103` (функция `handle_voice` целиком)

- [ ] **Step 1: Добавить импорт**

В блок импортов `main.py` (после `from openai import OpenAI`, строка ~18):

```python
import asr
```

- [ ] **Step 2: Общий помощник распознавания**

Вставить в `main.py` ПЕРЕД `handle_voice`:

```python
async def _transcribe_and_reply(update: Update, data: bytes,
                                filename: str, emoji: str) -> str | None:
    """Распознаёт аудио, показывает текст пользователю (без Markdown, кусками).
    Возвращает текст или None, если распознать не удалось (пользователю уже ответили)."""
    try:
        text = await asyncio.to_thread(asr.transcribe, data, filename)
    except asr.RateLimited:
        await update.message.reply_text(
            "⏳ Слишком много запросов — подождите минуту и отправьте ещё раз, "
            "или напишите текстом."
        )
        return None
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Не удалось распознать — попробуйте ещё раз или напишите текстом."
        )
        return None

    if not text:
        await update.message.reply_text(
            "🤔 Не расслышал — повторите, пожалуйста, или напишите текстом."
        )
        return None

    # без parse_mode: в сыром транскрипте могут быть _ и *, ломающие Markdown
    for chunk in asr.split_for_telegram(f"{emoji} «{text}»"):
        await update.message.reply_text(chunk)
    return text
```

- [ ] **Step 3: Заменить `handle_voice` целиком**

Старая функция (с вложенной `transcribe` на SpeechRecognition/pydub) удаляется, вместо неё:

```python
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    voice = update.message.voice
    if voice.duration and voice.duration > 600:
        await update.message.reply_text(
            "⏱ Запись длиннее 10 минут — расскажите короче или напишите текстом."
        )
        return

    await update.message.reply_text("🎤 Распознаю голос... ⏳")
    tg_file = await context.bot.get_file(voice.file_id)
    buf     = BytesIO()
    await tg_file.download_to_memory(buf)

    text = await _transcribe_and_reply(update, buf.getvalue(), "voice.ogg", "🎤")
    if text:
        await _process(update, context, session, text, f"[🎤 Голосовое] {text}")
```

- [ ] **Step 4: Проверить, что бот импортируется и старых зависимостей в коде нет**

Run (PowerShell, из `tzbot/`):
`$env:TELEGRAM_TOKEN='x'; $env:OPENROUTER_API_KEY='x'; $env:ALEXANDER_CHAT_ID='1'; python -c "import main; print('ok')"`
Expected: `ok` (env-заглушки нужны только для импорта)

Run: `python -m pytest test_asr.py -v` → 9 passed
Grep: в `main.py` не осталось `speech_recognition`, `pydub`, `recognize_google`.

- [ ] **Step 5: Commit**

```bash
git add tzbot/main.py
git commit -m "feat(tzbot): голосовые через Groq Whisper — показ без Markdown кусками, лимит 10 минут"
```

---

### Task 4: видеокружочки — `handle_video_note`

**Files:**
- Modify: `tzbot/main.py` (новый хендлер после `handle_voice`; регистрация в `main()`; текст в `handle_other`)

- [ ] **Step 1: Новый хендлер**

Вставить в `main.py` СРАЗУ ПОСЛЕ `handle_voice`:

```python
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if not session:
        await update.message.reply_text(**_no_session_reply(context))
        return

    await update.message.reply_text("🎥 Распознаю кружочек... ⏳")
    note    = update.message.video_note
    tg_file = await context.bot.get_file(note.file_id)
    buf     = BytesIO()
    await tg_file.download_to_memory(buf)

    text = await _transcribe_and_reply(update, buf.getvalue(), "note.mp4", "📹")
    if text:
        await _process(update, context, session, text, f"[📹 Кружочек] {text}")
```

(Кружочки Telegram ограничивает 60 секундами — проверка длительности не нужна.)

- [ ] **Step 2: Регистрация хендлера**

В `main()` — сейчас там:

```python
    app.add_handler(MessageHandler(filters.VOICE,        handle_voice))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_other))
```

Стало (VIDEO_NOTE обязательно ДО catch-all `handle_other`):

```python
    app.add_handler(MessageHandler(filters.VOICE,        handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE,   handle_video_note))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_other))
```

- [ ] **Step 3: Обновить подсказку в `handle_other`**

Заменить текст:

```python
        await update.message.reply_text(
            "📝 Я понимаю текст, голосовые, кружочки, изображения, PDF и ссылки.\n"
            "Напишите ответ, запишите голосовое или пришлите скриншот / файл."
        )
```

- [ ] **Step 4: Проверка импорта**

Run: `$env:TELEGRAM_TOKEN='x'; $env:OPENROUTER_API_KEY='x'; $env:ALEXANDER_CHAT_ID='1'; python -c "import main; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add tzbot/main.py
git commit -m "feat(tzbot): распознавание видеокружочков"
```

---

### Task 5: зачистка зависимостей и конфиг

**Files:**
- Modify: `tzbot/requirements.txt` — удалить строки `SpeechRecognition>=3.10.0` и `pydub>=0.25.1`
- Modify: `tzbot/nixpacks.toml` — из `nixPkgs` убрать `"ffmpeg"`: `nixPkgs = ["python311", "python311Packages.pip"]`
- Modify: `tzbot/.env.example` — добавить строки:

```
GROQ_API_KEY=gsk_your-groq-api-key-here
ASR_MODEL=whisper-large-v3
```

- [ ] **Step 1: Внести все три правки** (содержимое выше)

- [ ] **Step 2: Проверить, что бот не использует удалённое**

Grep по `tzbot/`: `speech_recognition|pydub|ffmpeg` → совпадений нет (кроме, возможно, plans/specs в docs).
Run: `python -m pytest test_asr.py -v` → 9 passed

- [ ] **Step 3: Commit**

```bash
git add tzbot/requirements.txt tzbot/nixpacks.toml tzbot/.env.example
git commit -m "chore(tzbot): убрать SpeechRecognition/pydub/ffmpeg, добавить GROQ_API_KEY и ASR_MODEL в env"
```

---

### Task 6: деплой и ручная приёмка (по критериям спеки)

Автотестами это не покрыть — нужны реальный ключ, Railway и Telegram.

- [ ] **Step 1: Ключ Groq** — зарегистрироваться на https://console.groq.com (из РФ может понадобиться VPN), создать API Key.
- [ ] **Step 2: Railway → Variables** — добавить `GROQ_API_KEY` (и при желании `ASR_MODEL`) ДО деплоя кода.
- [ ] **Step 3: Задеплоить** — `git push` (Railway подхватит сборку; убедиться, что билд прошёл без ffmpeg).
- [ ] **Step 4: Приёмка в Telegram** (критерии спеки, раздел 6):
  1. Голосовое 30–60 сек на русском → текст с пунктуацией, без пропусков (3–5 записей, включая шумную).
  2. Кружочек → распознан, попал в интервью с меткой `[📹 Кружочек]`.
  3. Ответ на минутное голосовое ≤ ~5 сек.
  4. Голосовое > 10 минут → вежливый отказ, API не вызывался (проверить по логам).
  5. Сломать `GROQ_API_KEY` в Railway → голосовое даёт «❌ Не удалось распознать…», текст в интервью работает; вернуть ключ.
  6. Билд без SpeechRecognition/pydub/ffmpeg прошёл, бот работает.
  7. Голосовое 5+ минут → транскрипт пришёл несколькими сообщениями; запись со словами-с-подчёркиваниями (продиктовать «нижнее подчёркивание») → показ не падает.
- [ ] **Step 5: Финальный коммит чекбоксов плана** — отметить выполненное, закоммитить план.
