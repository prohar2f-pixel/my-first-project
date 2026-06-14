import os
import asyncio
import logging
import json
import base64
import re
from io import BytesIO
from datetime import date

import psycopg2
import psycopg2.pool

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
ALEXANDER_CHAT_ID = int(os.environ["ALEXANDER_CHAT_ID"])

claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

URL_RE = re.compile(r'https?://[^\s]+')

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


# ─── DATABASE ─────────────────────────────────────────────────────────────────

def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10, os.environ["DATABASE_URL"]
        )
    return _pool


def _exec(sql: str, params: tuple = (), fetch: bool = False):
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchone() if fetch else None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def db_init():
    _exec("""
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id    BIGINT PRIMARY KEY,
            site_type  TEXT,
            first_msg  TEXT DEFAULT '',
            steps      TEXT DEFAULT '[]',
            cur_q      TEXT DEFAULT '',
            updated_at BIGINT DEFAULT extract(epoch from now())::BIGINT
        )
    """)


def db_get(chat_id: int) -> dict | None:
    row = _exec(
        "SELECT site_type, first_msg, steps, cur_q FROM sessions WHERE chat_id=%s",
        (chat_id,), fetch=True
    )
    if not row:
        return None
    return {
        "site_type": row[0],
        "first_msg": row[1],
        "steps": json.loads(row[2]),
        "cur_q": row[3],
    }


def db_save(chat_id: int, *, site_type: str, first_msg: str, steps: list, cur_q: str):
    _exec("""
        INSERT INTO sessions (chat_id, site_type, first_msg, steps, cur_q)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET
            site_type  = EXCLUDED.site_type,
            first_msg  = EXCLUDED.first_msg,
            steps      = EXCLUDED.steps,
            cur_q      = EXCLUDED.cur_q,
            updated_at = extract(epoch from now())::BIGINT
    """, (chat_id, site_type, first_msg,
          json.dumps(steps, ensure_ascii=False), cur_q))


def db_delete(chat_id: int):
    _exec("DELETE FROM sessions WHERE chat_id=%s", (chat_id,))


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

SITE_TYPES = {
    "landing":   "🎯 Лендинг",
    "shop":      "🛒 Интернет-магазин",
    "corporate": "🏢 Корпоративный сайт",
    "portfolio": "🎨 Портфолио",
    "vizitka":   "💼 Сайт-визитка",
    "other":     "💡 Другой тип",
}

BASE_SYSTEM = f"""Ты — ИИ-помощник для сбора технического задания (ТЗ) на разработку сайта. Работаешь от имени Александра Прохорова — веб-разработчика.

Сегодняшняя дата: {date.today().strftime('%d.%m.%Y')}

## ТВОЯ ЗАДАЧА
Провести дружелюбное интервью с клиентом и собрать полное ТЗ. Задавай по ОДНОМУ вопросу за раз, жди ответа.

## ТЕМЫ ДЛЯ ПОКРЫТИЯ:
1. Бизнес — чем занимается, кто клиенты, цель сайта
2. Дизайн — стиль, цвета, примеры сайтов которые нравятся (принимаем ссылки, скриншоты, картинки)
3. Структура — какие разделы и страницы нужны
4. Контент — что есть (тексты, фото, логотип), что нужно создать
5. Интеграции — форма заявки, оплата, CRM, чат, аналитика, карта
6. Данные о клиентах — что собирать (имя, телефон, email и т.д.)
7. Воронки — pop-up, кнопки призыва к действию, автоответы на заявки

## ПРАВИЛА
- Начни с тёплого приветствия (упомяни выбранный тип сайта) и первого вопроса о бизнесе
- Один вопрос за раз — не засыпай клиента списком
- Если пользователь прислал изображение — проанализируй стиль и визуальные элементы, упомяни что увидел, продолжи интервью
- Если пользователь прислал ссылку — прокомментируй что узнал о сайте, продолжи интервью
- Если ответ расплывчатый — уточни конкретнее
- Когда все 7 тем закрыты — напиши маркер ТЗ_ГОТОВО на отдельной строке, затем выдай полное ТЗ

## ШАБЛОН ТЗ (писать только после закрытия всех тем):

ТЗ_ГОТОВО
# Техническое задание на разработку сайта
Дата: {date.today().strftime('%d.%m.%Y')}

## 1. О бизнесе
[подробно]

## 2. Цель сайта
[подробно]

## 3. Целевая аудитория
[подробно]

## 4. Дизайн и стиль
[цвета, настроение, примеры]

## 5. Структура сайта
[список разделов с кратким описанием]

## 6. Контент
[что есть, что нужно подготовить]

## 7. Технические интеграции
[список]

## 8. Сбор данных о клиентах
[поля форм]

## 9. Воронки и конверсия
[кнопки, pop-up, автоответы]

## 10. Дополнительные пожелания
[всё остальное]"""

SITE_TYPE_HINTS = {
    "landing":   "Клиент выбрал: Лендинг. Фокусируй вопросы на целевом действии, оффере и воронке продаж.",
    "shop":      "Клиент выбрал: Интернет-магазин. Уточни количество товаров, категории, оплату, доставку, личный кабинет.",
    "corporate": "Клиент выбрал: Корпоративный сайт. Фокусируй на разделах компании, команде, услугах, новостях.",
    "portfolio": "Клиент выбрал: Портфолио. Уточни какие работы показывать, нужен ли блог, форма для заказа.",
    "vizitka":   "Клиент выбрал: Сайт-визитка (1–3 страницы). Фокусируй на деятельности, контактах, форме связи.",
    "other":     "Клиент выбрал: Другой тип. Сначала уточни что именно он хочет, затем адаптируй вопросы.",
}


def build_system(site_type: str) -> str:
    hint = SITE_TYPE_HINTS.get(site_type, "")
    return f"{BASE_SYSTEM}\n\n## ТИП САЙТА\n{hint}"


# ─── KEYBOARDS ────────────────────────────────────────────────────────────────

def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(SITE_TYPES["landing"],   callback_data="type_landing"),
         InlineKeyboardButton(SITE_TYPES["shop"],      callback_data="type_shop")],
        [InlineKeyboardButton(SITE_TYPES["corporate"], callback_data="type_corporate"),
         InlineKeyboardButton(SITE_TYPES["portfolio"], callback_data="type_portfolio")],
        [InlineKeyboardButton(SITE_TYPES["vizitka"],   callback_data="type_vizitka"),
         InlineKeyboardButton(SITE_TYPES["other"],     callback_data="type_other")],
    ])


def nav_keyboard(has_prev: bool) -> InlineKeyboardMarkup | None:
    if not has_prev:
        return None
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Вернуться к предыдущему вопросу", callback_data="go_back")]
    ])


# ─── URL ENRICHMENT ───────────────────────────────────────────────────────────

def fetch_url_info(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title")
        desc = soup.find("meta", attrs={"name": "description"})
        info = f"[Сайт: {url}"
        if title:
            info += f" | {title.get_text(strip=True)}"
        if desc and desc.get("content"):
            info += f" — {desc['content'][:200]}"
        info += "]"
        return info
    except Exception as e:
        logger.warning(f"fetch_url_info {url}: {e}")
        return f"[Ссылка: {url}]"


# ─── CLAUDE ───────────────────────────────────────────────────────────────────

def build_messages(type_label: str, first_msg: str, steps: list, user_content) -> list:
    msgs = [
        {"role": "user",      "content": f"Я хочу {type_label}"},
        {"role": "assistant", "content": first_msg},
    ]
    for step in steps:
        msgs.append({"role": "user",      "content": step["user"]})
        msgs.append({"role": "assistant", "content": step["bot"]})
    msgs.append({"role": "user", "content": user_content})
    return msgs


def call_claude_sync(system: str, messages: list, max_tokens: int = 800) -> str:
    resp = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return resp.content[0].text


# ─── CORE PROCESS ─────────────────────────────────────────────────────────────

async def _process(update: Update, context: ContextTypes.DEFAULT_TYPE,
                   session: dict, user_content, user_label: str):
    """Send user input to Claude, save step, reply with nav keyboard."""
    type_label = SITE_TYPES.get(session["site_type"], "Сайт")
    system     = build_system(session["site_type"])
    messages   = build_messages(type_label, session["first_msg"], session["steps"], user_content)
    chat_id    = update.effective_chat.id

    try:
        reply = await asyncio.to_thread(call_claude_sync, system, messages, 2000)
    except Exception as e:
        logger.error(f"Claude error: {e}", exc_info=True)
        try:
            await update.message.reply_text("❌ Ошибка. Попробуй ещё раз или напиши /reset")
        except Exception:
            pass
        return

    if "ТЗ_ГОТОВО" in reply:
        await update.message.reply_text("✅ Отлично! Формирую ваше ТЗ... ⏳")
        tz_text = reply.split("ТЗ_ГОТОВО", 1)[1].strip()

        bio = BytesIO(tz_text.encode("utf-8"))
        await update.message.reply_document(
            document=bio,
            filename="ТЗ_на_сайт.txt",
            caption=(
                f"✅ Ваше ТЗ на *{type_label}* готово!\n\n"
                "Передайте файл Александру или напишите ему:\n"
                "👉 @alex\\_prohar"
            ),
            parse_mode="Markdown",
        )

        user     = update.effective_user
        username = f"@{user.username}" if user.username else "без username"
        await context.bot.send_message(
            chat_id=ALEXANDER_CHAT_ID,
            text=(
                f"🔔 Новая заявка с ТЗ!\n\n"
                f"От: {user.full_name} ({username})\n"
                f"Тип: {type_label}\n\n"
                f"Превью:\n{tz_text[:600]}..."
            ),
        )
        bio2 = BytesIO(tz_text.encode("utf-8"))
        await context.bot.send_document(
            chat_id=ALEXANDER_CHAT_ID,
            document=bio2,
            filename=f"ТЗ_{user.full_name}.txt",
        )

        db_delete(chat_id)
        return

    new_steps = session["steps"] + [
        {"question": session["cur_q"], "user": user_label, "bot": reply}
    ]
    db_save(chat_id,
            site_type=session["site_type"],
            first_msg=session["first_msg"],
            steps=new_steps,
            cur_q=reply)

    await update.message.reply_text(reply, reply_markup=nav_keyboard(len(new_steps) > 0))


def _no_session_reply(session, context):
    """Return kwargs for "session lost" or "not started" message."""
    site_type = context.user_data.get("site_type") if not session else None
    if site_type:
        label = SITE_TYPES.get(site_type, "Сайт")
        return {
            "text": (
                f"⚠️ Сессия прервалась — бот перезапускался, история диалога сброшена.\n\n"
                f"Вы выбирали: *{label}*\n\nНачнём заново 👇"
            ),
            "parse_mode": "Markdown",
            "reply_markup": start_keyboard(),
        }
    return {
        "text": "👋 Нажмите /start чтобы начать составление ТЗ.",
        "reply_markup": start_keyboard(),
    }


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_delete(update.effective_chat.id)
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Я помогу составить техническое задание на ваш сайт.\n\n"
        "Это займёт 5–10 минут. Задам несколько вопросов, а в конце пришлю готовое ТЗ.\n\n"
        "*Какой сайт вы хотите создать?*",
        parse_mode="Markdown",
        reply_markup=start_keyboard(),
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_delete(update.effective_chat.id)
    context.user_data.clear()
    await update.message.reply_text("🔄 Начинаем заново!", reply_markup=start_keyboard())


async def handle_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query      = update.callback_query
    await query.answer()

    site_type  = query.data.replace("type_", "")
    chat_id    = query.message.chat_id
    type_label = SITE_TYPES.get(site_type, "Сайт")

    context.user_data["site_type"] = site_type
    await query.edit_message_text(f"Отлично, выбрано: *{type_label}*\n\nНачинаем! ⏳", parse_mode="Markdown")

    system = build_system(site_type)
    try:
        first_msg = await asyncio.to_thread(
            call_claude_sync, system,
            [{"role": "user", "content": f"Я хочу {type_label}"}], 600
        )
        db_save(chat_id, site_type=site_type, first_msg=first_msg, steps=[], cur_q=first_msg)
        await query.message.reply_text(first_msg)
    except Exception as e:
        logger.error(f"handle_type_callback: {e}", exc_info=True)
        await query.message.reply_text("❌ Ошибка. Попробуй ещё раз /start")


async def handle_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query   = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    session = db_get(chat_id)
    if not session or not session["steps"]:
        await query.message.reply_text("↩️ Уже в самом начале — вернуться некуда.")
        return

    last_step = session["steps"][-1]
    new_steps = session["steps"][:-1]
    prev_q    = last_step["question"]

    db_save(chat_id,
            site_type=session["site_type"],
            first_msg=session["first_msg"],
            steps=new_steps,
            cur_q=prev_q)

    await query.message.reply_text(
        f"↩️ Вернулись к предыдущему вопросу:\n\n{prev_q}",
        reply_markup=nav_keyboard(len(new_steps) > 0),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id  = update.effective_chat.id
    session  = db_get(chat_id)

    if not session:
        await update.message.reply_text(**_no_session_reply(session, context))
        return

    user_text = update.message.text

    # Enrich URLs found in the message
    urls = URL_RE.findall(user_text)
    if urls:
        await update.message.reply_text("🔗 Смотрю ссылку... ⏳")
        url_infos = await asyncio.gather(
            *[asyncio.to_thread(fetch_url_info, u) for u in urls]
        )
        enriched = user_text + "\n\n" + "\n".join(url_infos)
    else:
        enriched = user_text

    await _process(update, context, session, enriched, user_text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)

    if not session:
        await update.message.reply_text(**_no_session_reply(session, context))
        return

    await update.message.reply_text("📸 Анализирую изображение... ⏳")

    photo   = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    buf     = BytesIO()
    await tg_file.download_to_memory(buf)
    img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

    caption = update.message.caption or ""
    label   = f"[📸 Изображение]{' — ' + caption if caption else ''}"

    user_content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64},
        },
        {
            "type": "text",
            "text": (
                "Вот визуальный референс — пример того, что мне нравится по стилю/дизайну."
                + (f" {caption}" if caption else "")
                + " Проанализируй что видишь (стиль, цвета, компоновку) и продолжи интервью."
            ),
        },
    ]
    await _process(update, context, session, user_content, label)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)

    if not session:
        await update.message.reply_text(**_no_session_reply(session, context))
        return

    doc  = update.message.document
    mime = doc.mime_type or ""

    if "pdf" in mime:
        await update.message.reply_text("📄 Читаю документ... ⏳")
        tg_file = await context.bot.get_file(doc.file_id)
        buf     = BytesIO()
        await tg_file.download_to_memory(buf)
        raw     = buf.getvalue()

        def extract_pdf(data: bytes) -> str:
            import pdfplumber
            texts = []
            with pdfplumber.open(BytesIO(data)) as pdf:
                for page in pdf.pages[:10]:
                    t = page.extract_text() or ""
                    if t:
                        texts.append(t)
                    page.flush_cache()
            return "\n".join(texts)[:3000]

        try:
            pdf_text = await asyncio.to_thread(extract_pdf, raw)
        except Exception as e:
            logger.error(f"PDF extract: {e}")
            await update.message.reply_text("❌ Не удалось прочитать PDF. Опишите содержимое текстом.")
            return

        label        = f"[📄 PDF: {doc.file_name}]"
        user_content = f"{label}\n\n{pdf_text}"
        await _process(update, context, session, user_content, label)

    elif mime.startswith("image/"):
        await update.message.reply_text("📸 Анализирую изображение... ⏳")
        tg_file = await context.bot.get_file(doc.file_id)
        buf     = BytesIO()
        await tg_file.download_to_memory(buf)
        img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

        caption = update.message.caption or ""
        label   = f"[📸 Изображение (файл)]{' — ' + caption if caption else ''}"

        user_content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": img_b64},
            },
            {
                "type": "text",
                "text": (
                    "Вот визуальный референс."
                    + (f" {caption}" if caption else "")
                    + " Проанализируй стиль и продолжи интервью."
                ),
            },
        ]
        await _process(update, context, session, user_content, label)

    else:
        await update.message.reply_text(
            f"📎 Файл *{doc.file_name}* получен, но я умею читать только PDF и изображения.\n\n"
            "Пришлите скриншот или ссылку — или опишите текстом.",
            parse_mode="Markdown",
        )


async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = db_get(chat_id)
    if session:
        await update.message.reply_text(
            "📝 Я понимаю текст, изображения, PDF и ссылки.\n"
            "Напишите ответ или пришлите скриншот / файл."
        )
    else:
        await update.message.reply_text(**_no_session_reply(session, context))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)


async def post_init(app: Application) -> None:
    db_init()
    await app.bot.set_my_commands([
        BotCommand("start", "Начать сбор ТЗ"),
        BotCommand("reset", "Начать заново"),
    ])


def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(CallbackQueryHandler(handle_type_callback, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(handle_back_callback, pattern="^go_back$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_other))

    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
