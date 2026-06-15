import json
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from parsers import Order

log = logging.getLogger(__name__)

SOURCE_EMOJI = {
    "FL.ru": "🟠",
    "Habr Freelance": "🟢",
    "Kwork": "🔵",
}


def order_keyboard(order: Order) -> InlineKeyboardMarkup:
    data = json.dumps({"id": order.id, "t": order.title[:40], "d": order.description[:200], "s": order.source})
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔗 Открыть заказ", url=order.url),
            InlineKeyboardButton(text="✍️ Написать отклик", callback_data=f"reply:{order.id}"),
        ]
    ])


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
        f"{desc}"
    )

    try:
        await bot.send_message(
            user_id,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=order_keyboard(order),
        )
    except Exception as e:
        log.error(f"Не удалось отправить уведомление: {e}")
