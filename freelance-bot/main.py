import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, USER_ID, CHECK_INTERVAL, KEYWORDS, TG_CHANNELS
from database import init_db, is_seen, mark_seen
from filters import matches
from notifier import send_order
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


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != USER_ID:
        return
    interval_min = CHECK_INTERVAL // 60
    await message.answer(
        "Бот запущен!\n\n"
        f"Мониторю: FL.ru, Habr Freelance, Kwork, Telegram-каналы\n"
        f"Интервал проверки: каждые {interval_min} мин\n"
        f"Ключевых слов: {len(KEYWORDS)}\n\n"
        "Команды:\n"
        "/keywords — список ключевых слов\n"
        "/channels — список каналов\n"
        "/check — проверить прямо сейчас"
    )


@dp.message(Command("keywords"))
async def cmd_keywords(message: Message):
    if message.from_user.id != USER_ID:
        return
    kw_list = "\n".join(f"• {kw}" for kw in KEYWORDS)
    await message.answer(f"Ключевые слова:\n\n{kw_list}")


@dp.message(Command("channels"))
async def cmd_channels(message: Message):
    if message.from_user.id != USER_ID:
        return
    if TG_CHANNELS:
        ch_list = "\n".join(f"• {ch}" for ch in TG_CHANNELS)
        await message.answer(f"Telegram-каналы:\n\n{ch_list}")
    else:
        await message.answer("Telegram-каналы не настроены. Добавь их в .env файл.")


@dp.message(Command("check"))
async def cmd_check(message: Message):
    if message.from_user.id != USER_ID:
        return
    await message.answer("Запускаю проверку...")
    await check_all()
    await message.answer("Проверка завершена.")


async def check_all():
    log.info("Запускаю проверку всех источников...")

    results = await asyncio.gather(
        flru.fetch(),
        habr.fetch(),
        kwork.fetch(),
        tg.fetch(TG_CHANNELS),
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
            mark_seen(order.id, order.source)
            if matches(order.title + " " + order.description):
                await send_order(bot, USER_ID, order)
                total_new += 1
                await asyncio.sleep(0.5)  # небольшая пауза между сообщениями

    log.info(f"Готово. Новых подходящих заказов: {total_new}")


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
