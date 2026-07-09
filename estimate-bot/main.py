"""Telegram bot handlers — no arithmetic logic."""

import asyncio
import logging
from decimal import Decimal

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_TOKEN, ALLOWED_USER_IDS, DEFAULT_REGION
from calculator import LineInput, build_and_verify
from pdf_extract import extract_positions_from_pdf, normalize_position
from search import search_price
from excel_report import export_to_excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    user_id = update.effective_user.id
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("❌ Доступ запрещен.")
        return

    text = """👋 Привет! Я бот для расчёта смет объектов.

**Что я делаю:**
1. Загружаешь PDF-смету или список позиций
2. Я извлекаю работы и материалы
3. Ищу рыночные цены в интернете
4. Считаю суммы (Decimal, без ошибок)
5. ✅ Перепроверяю расчёты дважды
6. Отправляю Excel + итог в чат

**Команды:**
/start — справка
/cancel — отменить
/region <регион> — выбрать регион для поиска цен (по умолчанию Москва)

**Как использовать:**
→ Отправь PDF-файл

⚠️ **Важно:** Цены — это ориентир рынка. Суммы пересчитываются калькулятором **дважды** перед отправкой отчёта.
"""

    await update.message.reply_text(text, parse_mode="markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel command."""
    await update.message.reply_text("❌ Отменено.")


async def handle_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/region command."""
    if not context.args:
        await update.message.reply_text(f"📍 Текущий регион: {DEFAULT_REGION}\n/region <название> для смены")
        return

    region = " ".join(context.args)
    context.user_data["region"] = region
    await update.message.reply_text(f"✅ Регион установлен: {region}")


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF file upload."""
    user_id = update.effective_user.id
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("❌ Доступ запрещен.")
        return

    # Download file
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    pdf_path = f"/tmp/{document.file_name}"
    await file.download_to_drive(pdf_path)

    # Extract positions
    await update.message.reply_text("⏳ Извлекаю позиции из PDF...")
    try:
        raw_positions = await extract_positions_from_pdf(pdf_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при извлечении PDF: {e}")
        return

    # Normalize
    positions = [normalize_position(p) for p in raw_positions]
    positions = [p for p in positions if p]

    if not positions:
        await update.message.reply_text("❌ Не найдены позиции в PDF.")
        return

    await update.message.reply_text(f"✅ Извлечено: {len(positions)} позиций\n⏳ Ищу цены...")

    # Search prices (with semaphore to avoid rate limit)
    region = context.user_data.get("region", DEFAULT_REGION)
    semaphore = asyncio.Semaphore(3)

    async def search_with_limit(pos):
        async with semaphore:
            try:
                price_data = await search_price(pos.name, pos.unit, region)
                pos.unit_price = price_data.get("price_typical")
                pos.price_min = price_data.get("price_min")
                pos.price_max = price_data.get("price_max")
                pos.confidence = price_data.get("confidence", "none")
                pos.source = price_data.get("source")
                return pos
            except Exception as e:
                logger.error(f"Price search failed for {pos.name}: {e}")
                return pos

    positions = await asyncio.gather(*[search_with_limit(p) for p in positions])

    await update.message.reply_text("✅ Цены найдены.\n⏳ Вычисляю итоги...")

    # Calculate
    try:
        estimate = build_and_verify(positions)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при расчёте: {e}")
        return

    if not estimate.verified:
        await update.message.reply_text(
            f"❌ **Ошибка внутреннего расчёта:** {estimate.verify_error}\n\n"
            "Отчёт не сформирован. Попробуйте ещё раз или напишите разработчику."
        )
        return

    # Export Excel
    try:
        excel_file = export_to_excel(estimate, region)
    except RuntimeError as e:
        await update.message.reply_text(f"❌ Ошибка при экспорте: {e}")
        return

    # Send caption + file
    caption = estimate.caption_totals()
    await update.message.reply_text(f"✅ **Расчёт выполнен:**\n\n{caption}", parse_mode="markdown")

    with open(excel_file, "rb") as f:
        await update.message.reply_document(f, filename=excel_file)

    await update.message.reply_text("✨ Готово!")


def main():
    """Run bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("region", handle_region))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    logger.info("Starting bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
