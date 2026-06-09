import logging
from aiogram import Bot
from parsers import Order

log = logging.getLogger(__name__)

SOURCE_EMOJI = {
    "FL.ru": "🟠",
    "Habr Freelance": "🟢",
    "Kwork": "🔵",
}


async def send_order(bot: Bot, user_id: int, order: Order):
    emoji = SOURCE_EMOJI.get(order.source, "🔔")
    price_line = f"\n💰 <b>{order.price}</b>" if order.price else ""
    desc = order.description[:400].strip()
    if len(order.description) > 400:
        desc += "…"

    text = (
        f"{emoji} <b>{order.source}</b>\n\n"
        f"<b>{order.title}</b>"
        f"{price_line}\n\n"
        f"{desc}\n\n"
        f'<a href="{order.url}">Открыть заказ →</a>'
    )

    try:
        await bot.send_message(
            user_id,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception as e:
        log.error(f"Не удалось отправить уведомление: {e}")
