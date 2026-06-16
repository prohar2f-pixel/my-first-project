import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, USER_ID, CHECK_INTERVAL
from database import (
    init_db, is_seen, mark_seen, get_order,
    get_channels, add_channel, remove_channel,
    get_keywords, add_keyword, remove_keyword,
)
from filters import matches
from notifier import send_order
from responder import generate_response
import parsers.flru as flru
import parsers.habr as habr
import parsers.kwork as kwork
import parsers.tg_channels as tg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Проверить сейчас", callback_data="check"),
        ],
        [
            InlineKeyboardButton(text="📋 Ключевые слова", callback_data="keywords"),
            InlineKeyboardButton(text="📢 Каналы", callback_data="channels"),
        ],
        [
            InlineKeyboardButton(text="📊 Статус", callback_data="status"),
        ],
    ])


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != USER_ID:
        return
    interval_min = CHECK_INTERVAL // 60
    await message.answer(
        f"🤖 <b>Freelance Monitor Bot</b>\n\n"
        f"Мониторю: FL.ru, Habr Freelance, Kwork, TG-каналы\n"
        f"Интервал: каждые {interval_min} мин\n"
        f"Ключевых слов: {len(get_keywords())}",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("keywords"))
async def cmd_keywords(message: Message):
    if message.from_user.id != USER_ID:
        return
    await show_keywords(message)


@dp.message(Command("channels"))
async def cmd_channels(message: Message):
    if message.from_user.id != USER_ID:
        return
    await show_channels(message)


@dp.message(Command("addchannel"))
async def cmd_addchannel(message: Message):
    if message.from_user.id != USER_ID:
        return
    arg = message.text.partition(" ")[2].strip()
    if not arg:
        await message.answer("Используй: /addchannel @username")
        return
    if not arg.startswith("@"):
        arg = "@" + arg
    if add_channel(arg):
        await message.answer(f"✅ Канал {arg} добавлен.")
    else:
        await message.answer(f"Канал {arg} уже в списке.")


@dp.message(Command("delchannel"))
async def cmd_delchannel(message: Message):
    if message.from_user.id != USER_ID:
        return
    arg = message.text.partition(" ")[2].strip()
    if not arg:
        await message.answer("Используй: /delchannel @username")
        return
    if not arg.startswith("@"):
        arg = "@" + arg
    if remove_channel(arg):
        await message.answer(f"🗑 Канал {arg} удалён.")
    else:
        await message.answer(f"Канал {arg} не найден.")


@dp.message(Command("addkeyword"))
async def cmd_addkeyword(message: Message):
    if message.from_user.id != USER_ID:
        return
    arg = message.text.partition(" ")[2].strip()
    if not arg:
        await message.answer("Используй: /addkeyword слово или фраза")
        return
    if add_keyword(arg):
        await message.answer(f"✅ Ключевое слово «{arg}» добавлено.")
    else:
        await message.answer(f"«{arg}» уже в списке.")


@dp.message(Command("delkeyword"))
async def cmd_delkeyword(message: Message):
    if message.from_user.id != USER_ID:
        return
    arg = message.text.partition(" ")[2].strip()
    if not arg:
        await message.answer("Используй: /delkeyword слово или фраза")
        return
    if remove_keyword(arg):
        await message.answer(f"🗑 «{arg}» удалено.")
    else:
        await message.answer(f"«{arg}» не найдено.")


@dp.message(Command("check"))
async def cmd_check(message: Message):
    if message.from_user.id != USER_ID:
        return
    msg = await message.answer("🔄 Запускаю проверку...")
    count = await check_all()
    await msg.edit_text(
        f"✅ Проверка завершена.\n"
        f"Новых подходящих заказов: <b>{count}</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "check")
async def cb_check(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    await callback.message.edit_text("🔄 Запускаю проверку...")
    count = await check_all()
    await callback.message.edit_text(
        f"✅ Проверка завершена.\n"
        f"Новых подходящих заказов: <b>{count}</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "keywords")
async def cb_keywords(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    await show_keywords(callback.message)


@dp.callback_query(F.data == "channels")
async def cb_channels(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    await show_channels(callback.message)


@dp.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    interval_min = CHECK_INTERVAL // 60
    await callback.message.edit_text(
        f"📊 <b>Статус бота</b>\n\n"
        f"✅ FL.ru — активен\n"
        f"✅ Habr Freelance — активен\n"
        f"✅ Kwork — активен\n"
        f"✅ TG-каналов: {len(get_channels())}\n\n"
        f"⏱ Интервал проверки: каждые {interval_min} мин\n"
        f"🔑 Ключевых слов: {len(get_keywords())}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("reply:"))
async def cb_reply(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer("Генерирую отклик...")
    order_id = callback.data.split(":", 1)[1]
    order = get_order(order_id)
    if not order:
        await callback.message.answer("Данные заказа не найдены.")
        return
    msg = await callback.message.answer("✍️ Генерирую отклик через Claude...")
    try:
        response = await generate_response(order["title"], order["description"], order["source"])
        await msg.edit_text(
            f"✍️ <b>Отклик готов:</b>\n\n{response}",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.edit_text(f"Ошибка генерации: {e}")


@dp.callback_query(F.data == "back")
async def cb_back(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    interval_min = CHECK_INTERVAL // 60
    await callback.message.edit_text(
        f"🤖 <b>Freelance Monitor Bot</b>\n\n"
        f"Мониторю: FL.ru, Habr Freelance, Kwork, TG-каналы\n"
        f"Интервал: каждые {interval_min} мин\n"
        f"Ключевых слов: {len(get_keywords())}",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


async def show_keywords(message: Message):
    kw_list = "\n".join(f"• {kw}" for kw in get_keywords())
    await message.answer(
        f"🔑 <b>Ключевые слова:</b>\n\n{kw_list}\n\n"
        f"Добавить: <code>/addkeyword слово</code>\n"
        f"Удалить: <code>/delkeyword слово</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]),
        parse_mode="HTML",
    )


async def show_channels(message: Message):
    channels = get_channels()
    if channels:
        ch_list = "\n".join(f"• {ch}" for ch in channels)
        text = f"📢 <b>Telegram-каналы:</b>\n\n{ch_list}"
    else:
        text = "Telegram-каналы не настроены."
    text += "\n\nДобавить: <code>/addchannel @канал</code>\nУдалить: <code>/delchannel @канал</code>"
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]),
        parse_mode="HTML",
    )


async def check_all() -> int:
    log.info("Запускаю проверку всех источников...")

    results = await asyncio.gather(
        flru.fetch(),
        habr.fetch(),
        kwork.fetch(),
        tg.fetch(get_channels()),
        return_exceptions=True,
    )

    total_new = 0
    for orders in results:
        if isinstance(orders, Exception):
            log.error(f"Ошибка парсера: {orders}")
            continue
        for order in orders:
            if is_seen(order.id):
                continue
            mark_seen(order.id, order.source, order.title, order.description)
            if matches(order.title + " " + order.description):
                await send_order(bot, USER_ID, order)
                total_new += 1
                await asyncio.sleep(0.5)

    log.info(f"Готово. Новых подходящих заказов: {total_new}")
    return total_new


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("ОШИБКА: BOT_TOKEN не задан в .env файле!")
        return
    if not USER_ID:
        print("ОШИБКА: USER_ID не задан в .env файле!")
        return

    init_db()
    log.info("База данных инициализирована.")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_all, "interval", seconds=CHECK_INTERVAL, id="check_all")
    scheduler.start()
    log.info(f"Планировщик запущен. Интервал: {CHECK_INTERVAL} сек.")

    await check_all()

    log.info("Бот запущен и ждёт заказов...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
