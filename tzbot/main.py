import os
import asyncio
import logging
from io import BytesIO
from datetime import date

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

conversations: dict[int, list] = {}

SITE_TYPES = {
    "landing": "🎯 Лендинг",
    "shop": "🛒 Интернет-магазин",
    "corporate": "🏢 Корпоративный сайт",
    "portfolio": "🎨 Портфолио",
    "vizitka": "💼 Сайт-визитка",
    "other": "💡 Другой тип",
}

BASE_SYSTEM = f"""Ты — ИИ-помощник для сбора технического задания (ТЗ) на разработку сайта. Работаешь от имени Александра Прохорова — веб-разработчика.

Сегодняшняя дата: {date.today().strftime('%d.%m.%Y')}

## ТВОЯ ЗАДАЧА
Провести дружелюбное интервью с клиентом и собрать полное ТЗ для разработки его сайта. Задавай по ОДНОМУ вопросу за раз, жди ответа.

## ТЕМЫ ДЛЯ ПОКРЫТИЯ:
1. Бизнес — чем занимается, кто клиенты, цель сайта
2. Дизайн — стиль, цвета, примеры сайтов которые нравятся
3. Структура — какие разделы и страницы нужны
4. Контент — что есть (тексты, фото, логотип), что нужно создать
5. Интеграции — форма заявки, оплата, CRM, чат, аналитика, карта
6. Данные о клиентах — что собирать (имя, телефон, email и т.д.)
7. Воронки — pop-up, кнопки призыва к действию, автоответы на заявки

## ПРАВИЛА
- Начни с тёплого приветствия (упомяни выбранный тип сайта) и первого вопроса о бизнесе
- Один вопрос за раз — не засыпай клиента списком
- Если ответ расплывчатый — уточни конкретнее
- Когда все 7 тем закрыты — напиши только маркер ТЗ_ГОТОВО на отдельной строке, затем сразу выдай полное ТЗ по шаблону ниже

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
[список разделов с кратким описанием каждого]

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
    "landing": "Клиент выбрал: Лендинг (одностраничный продающий сайт). Фокусируй вопросы на целевом действии, оффере и воронке продаж.",
    "shop": "Клиент выбрал: Интернет-магазин. Уточни количество товаров, категории, систему оплаты, доставку, личный кабинет покупателя.",
    "corporate": "Клиент выбрал: Корпоративный сайт. Фокусируй вопросы на разделах компании, команде, услугах, новостях и контактах.",
    "portfolio": "Клиент выбрал: Портфолио. Уточни какие работы показывать, хочет ли блог, форму для связи и заказа.",
    "vizitka": "Клиент выбрал: Сайт-визитка (небольшой сайт 1-3 страницы для представления специалиста или малого бизнеса). Фокусируй вопросы на описании деятельности, контактах, услугах и форме связи.",
    "other": "Клиент выбрал: Другой тип сайта. Сначала уточни что именно он хочет, затем адаптируй вопросы.",
}


def build_system_prompt(site_type: str) -> str:
    hint = SITE_TYPE_HINTS.get(site_type, "")
    return f"{BASE_SYSTEM}\n\n## ТИП САЙТА\n{hint}"


def start_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(SITE_TYPES["landing"], callback_data="type_landing"),
         InlineKeyboardButton(SITE_TYPES["shop"], callback_data="type_shop")],
        [InlineKeyboardButton(SITE_TYPES["corporate"], callback_data="type_corporate"),
         InlineKeyboardButton(SITE_TYPES["portfolio"], callback_data="type_portfolio")],
        [InlineKeyboardButton(SITE_TYPES["vizitka"], callback_data="type_vizitka"),
         InlineKeyboardButton(SITE_TYPES["other"], callback_data="type_other")],
    ]
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conversations.pop(chat_id, None)
    await update.message.reply_text(
        "👋 Привет! Я помогу составить техническое задание на ваш сайт.\n\n"
        "Это займёт 5–10 минут. Я задам несколько вопросов, а в конце пришлю готовое ТЗ.\n\n"
        "Для начала — *какой сайт вы хотите создать?*",
        parse_mode="Markdown",
        reply_markup=start_keyboard()
    )


async def handle_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    site_type = query.data.replace("type_", "")
    chat_id = query.message.chat_id
    type_label = SITE_TYPES.get(site_type, "Сайт")

    context.user_data["site_type"] = site_type
    conversations[chat_id] = []

    await query.edit_message_text(
        f"Отлично, выбрано: *{type_label}*\n\nНачинаем! ⏳",
        parse_mode="Markdown"
    )

    system = build_system_prompt(site_type)

    def call_claude():
        return claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": f"Я хочу {type_label}"}],
        )

    try:
        response = await asyncio.to_thread(call_claude)
        reply = response.content[0].text
        conversations[chat_id].append({"role": "assistant", "content": reply})
        await query.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Claude error in callback: {e}", exc_info=True)
        await query.message.reply_text("❌ Ошибка соединения. Попробуй ещё раз /start")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conversations.pop(chat_id, None)
    context.user_data.clear()
    await update.message.reply_text(
        "🔄 Начинаем заново!",
        reply_markup=start_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in conversations:
        await update.message.reply_text(
            "Нажми /start чтобы начать 👇",
            reply_markup=start_keyboard()
        )
        return

    site_type = context.user_data.get("site_type", "other")
    system = build_system_prompt(site_type)

    conversations[chat_id].append({"role": "user", "content": user_text})

    def call_claude():
        return claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=system,
            messages=conversations[chat_id],
        )

    try:
        response = await asyncio.to_thread(call_claude)
        reply = response.content[0].text
        conversations[chat_id].append({"role": "assistant", "content": reply})

        if "ТЗ_ГОТОВО" in reply:
            await update.message.reply_text("Отлично! Формирую ваше ТЗ... ⏳")

            tz_text = reply.split("ТЗ_ГОТОВО", 1)[1].strip()
            type_label = SITE_TYPES.get(site_type, "Сайт")

            bio = BytesIO(tz_text.encode("utf-8"))
            await update.message.reply_document(
                document=bio,
                filename="ТЗ_на_сайт.txt",
                caption=(
                    f"✅ Ваше ТЗ на *{type_label}* готово!\n\n"
                    "Передайте этот файл Александру или напишите ему напрямую:\n"
                    "👉 @alex\\_prohar"
                ),
                parse_mode="Markdown"
            )

            user = update.effective_user
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

            del conversations[chat_id]
            context.user_data.clear()
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"handle_message error: {e}", exc_info=True)
        try:
            await update.message.reply_text("❌ Ошибка. Попробуй ещё раз или напиши /reset")
        except Exception:
            pass


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "Начать сбор ТЗ"),
        BotCommand("reset", "Начать заново"),
    ])


def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(handle_type_callback, pattern="^type_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
