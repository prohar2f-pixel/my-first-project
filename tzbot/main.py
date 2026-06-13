import os
import logging
from io import BytesIO
from datetime import date

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
ALEXANDER_CHAT_ID = int(os.environ["ALEXANDER_CHAT_ID"])

claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

conversations: dict[int, list] = {}

SYSTEM_PROMPT = f"""Ты — ИИ-помощник для сбора технического задания (ТЗ) на разработку сайта. Работаешь от имени Александра Прохорова — веб-разработчика.

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
- Начни с тёплого приветствия и первого вопроса о бизнесе
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conversations[chat_id] = []

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Привет"}],
    )
    reply = response.content[0].text
    conversations[chat_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conversations.pop(chat_id, None)
    await update.message.reply_text("Начинаем заново! Напишите /start")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in conversations:
        await update.message.reply_text("Напишите /start чтобы начать")
        return

    conversations[chat_id].append({"role": "user", "content": user_text})

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=conversations[chat_id],
    )
    reply = response.content[0].text
    conversations[chat_id].append({"role": "assistant", "content": reply})

    if "ТЗ_ГОТОВО" in reply:
        await update.message.reply_text("Отлично! Формирую ваше ТЗ... ⏳")

        tz_text = reply.split("ТЗ_ГОТОВО", 1)[1].strip()

        # Отправляем клиенту
        bio = BytesIO(tz_text.encode("utf-8"))
        await update.message.reply_document(
            document=bio,
            filename="ТЗ_на_сайт.txt",
            caption=(
                "✅ Ваше техническое задание готово!\n\n"
                "Передайте этот файл Александру или напишите ему напрямую:\n"
                "👉 @alex_prohar"
            ),
        )

        # Уведомляем Александра
        user = update.effective_user
        username = f"@{user.username}" if user.username else "без username"
        await context.bot.send_message(
            chat_id=ALEXANDER_CHAT_ID,
            text=(
                f"🔔 Новая заявка с ТЗ!\n\n"
                f"От: {user.full_name} ({username})\n\n"
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
    else:
        await update.message.reply_text(reply)


def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
