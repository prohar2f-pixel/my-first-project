import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, USER_ID, CHECK_INTERVAL, OPENROUTER_API_KEY
from database import (
    init_db, is_seen, is_seen_fingerprint, is_seen_url, mark_seen, get_order,
    get_channels, add_channel, remove_channel,
    get_keywords, add_keyword, remove_keyword,
    get_profile_fields, set_profile_field,
    get_stats_by_source, _make_fingerprint,
)

MAX_PER_CYCLE = 5
MIN_TEXT_LEN  = 100

from filters import matches
from notifier import send_order
from responder import generate_response
from selection import round_robin
import parsers.flru as flru
import parsers.kwork as kwork
import parsers.tg_channels as tg
import parsers.freelanceru as freelanceru
import parsers.weblancer as weblancer
import parsers.freelancehunt as freelancehunt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

pending: dict[int, str] = {}

PROFILE_LABELS = {
    "name":      "👤 Имя",
    "title":     "🏷 Должность/роль",
    "location":  "📍 Локация",
    "services":  "🛠 Услуги и цены",
    "skills":    "💡 Навыки и стек",
    "contact":   "💬 Контакт (Telegram)",
    "tzbot":     "🤖 ТЗ-бот",
    "portfolio": "🌐 Портфолио",
    "style":     "✍️ Стиль откликов",
}


# ─── Клавиатуры ────────────────────────────────────────────────────────────────

def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Проверить сейчас", callback_data="check")],
        [InlineKeyboardButton(text="✍️ Написать отклик на вакансию", callback_data="reply_manual")],
        [
            InlineKeyboardButton(text="📋 Ключевые слова", callback_data="keywords"),
            InlineKeyboardButton(text="📢 Каналы", callback_data="channels"),
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
            InlineKeyboardButton(text="📊 Статус", callback_data="status"),
        ],
    ])


def channels_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🗑 {ch}", callback_data=f"delch:{ch}")]
        for ch in get_channels()
    ]
    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="addch_prompt")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def keywords_keyboard() -> InlineKeyboardMarkup:
    kws = get_keywords()
    buttons = [
        [InlineKeyboardButton(text=f"🗑 {kw}", callback_data=f"delkw:{kw[:30]}")]
        for kw in kws
    ]
    buttons.append([InlineKeyboardButton(text="➕ Добавить слово", callback_data="addkw_prompt")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"edit_profile:{key}")]
        for key, label in PROFILE_LABELS.items()
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Команды ───────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != USER_ID:
        return
    interval_min = CHECK_INTERVAL // 60
    api_status = "✅" if OPENROUTER_API_KEY else "❌ OPENROUTER_API_KEY не задан"
    await message.answer(
        f"🤖 <b>Freelance Monitor Bot</b>\n\n"
        f"Мониторю: FL.ru, Kwork, Freelance.ru, Weblancer, Freelancehunt, TG-каналы\n"
        f"Интервал: каждые {interval_min} мин\n"
        f"Ключевых слов: {len(get_keywords())}\n"
        f"Claude API: {api_status}",
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


@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    if message.from_user.id != USER_ID:
        return
    await show_profile(message)


@dp.message(Command("check"))
async def cmd_check(message: Message):
    if message.from_user.id != USER_ID:
        return
    msg = await message.answer("🔄 Запускаю проверку...")
    count = await check_all()
    await msg.edit_text(
        f"✅ Проверка завершена.\nНовых подходящих заказов: <b>{count}</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


# ─── Callback-кнопки ───────────────────────────────────────────────────────────

@dp.callback_query(F.data == "check")
async def cb_check(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    await callback.message.edit_text("🔄 Запускаю проверку...")
    count = await check_all()
    await callback.message.edit_text(
        f"✅ Проверка завершена.\nНовых подходящих заказов: <b>{count}</b>",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "reply_manual")
async def cb_reply_manual(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    if not OPENROUTER_API_KEY:
        await callback.answer("❌ OPENROUTER_API_KEY не задан в .env", show_alert=True)
        return
    pending[callback.from_user.id] = "vacancy"
    await callback.answer()
    await callback.message.answer(
        "Отправь текст вакансии следующим сообщением — напишу отклик."
    )


@dp.callback_query(F.data == "keywords")
async def cb_keywords(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    kws = get_keywords()
    kw_list = "\n".join(f"• {kw}" for kw in kws) if kws else "Список пуст."
    await callback.message.edit_text(
        f"🔑 <b>Ключевые слова ({len(kws)}):</b>\n\n{kw_list}\n\n"
        "Нажми на слово чтобы удалить, или добавь новое кнопкой ниже.",
        reply_markup=keywords_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "channels")
async def cb_channels(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    channels = get_channels()
    if channels:
        text = f"📢 <b>Telegram-каналы ({len(channels)}):</b>\n\nНажми на канал чтобы удалить, или добавь новый кнопкой ниже."
    else:
        text = "Каналы не настроены. Добавь первый канал кнопкой ниже."
    await callback.message.edit_text(text, reply_markup=channels_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    await show_profile(callback.message)


@dp.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    interval_min = CHECK_INTERVAL // 60
    api_ok = "✅ подключён" if OPENROUTER_API_KEY else "❌ ключ не задан"

    stats = get_stats_by_source()
    total = sum(cnt for _, cnt in stats)

    # Платформы отдельно от TG-каналов
    platforms = [(s, c) for s, c in stats if not s.startswith("TG")]
    tg_total  = sum(c for s, c in stats if s.startswith("TG"))

    platform_lines = "\n".join(f"  · {s}: <b>{c}</b>" for s, c in platforms) or "  нет данных"
    tg_line = f"  · TG-каналы: <b>{tg_total}</b>" if tg_total else "  · TG-каналы: нет данных"

    await callback.message.edit_text(
        f"📊 <b>Статус бота</b>\n\n"
        f"<b>Платформы:</b>\n{platform_lines}\n{tg_line}\n\n"
        f"📦 Всего обработано заказов: <b>{total}</b>\n"
        f"📢 TG-каналов: <b>{len(get_channels())}</b>\n"
        f"🔑 Ключевых слов: <b>{len(get_keywords())}</b>\n"
        f"⏱ Интервал: каждые <b>{interval_min} мин</b>\n"
        f"🤖 Claude API: {api_ok}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ]),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("reply:"))
async def cb_reply(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    if not OPENROUTER_API_KEY:
        await callback.answer("❌ OPENROUTER_API_KEY не задан в .env", show_alert=True)
        return
    await callback.answer("Генерирую отклик...")
    order_id = callback.data.split(":", 1)[1]
    order = get_order(order_id)
    if not order:
        pending[callback.from_user.id] = "vacancy"
        await callback.message.answer(
            "⚠️ Данные этого заказа не найдены (бот мог перезапуститься).\n\n"
            "Скопируй текст вакансии и отправь следующим сообщением — напишу отклик."
        )
        return
    msg = await callback.message.answer("✍️ Генерирую отклик через Claude...")
    try:
        response = await generate_response(order["title"], order["description"], order["source"])
        await msg.edit_text(f"✍️ <b>Отклик готов:</b>\n\n{response}", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка генерации:\n<code>{e}</code>", parse_mode="HTML")


@dp.callback_query(F.data.startswith("delch:"))
async def cb_delchannel_btn(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    name = callback.data.split(":", 1)[1]
    remove_channel(name)
    await callback.answer(f"Удалён {name}")
    text = (
        "📢 <b>Telegram-каналы:</b>\n\nНажми на канал чтобы удалить."
        if get_channels() else "Каналы не настроены."
    )
    await callback.message.edit_text(text, reply_markup=channels_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data.startswith("delkw:"))
async def cb_delkeyword_btn(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    word = callback.data.split(":", 1)[1]
    # Ищем полное слово по префиксу (т.к. обрезали до 30 символов в кнопке)
    for kw in get_keywords():
        if kw.startswith(word):
            remove_keyword(kw)
            await callback.answer(f"Удалено: {kw}")
            break
    else:
        await callback.answer("Не найдено")
    kws = get_keywords()
    kw_list = "\n".join(f"• {kw}" for kw in kws) if kws else "Список пуст."
    await callback.message.edit_text(
        f"🔑 <b>Ключевые слова ({len(kws)}):</b>\n\n{kw_list}\n\n"
        "Нажми на слово чтобы удалить, или добавь новое кнопкой ниже.",
        reply_markup=keywords_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "addch_prompt")
async def cb_addchannel_prompt(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    pending[callback.from_user.id] = "addchannel"
    await callback.answer()
    await callback.message.answer("Напиши @username канала следующим сообщением.")


@dp.callback_query(F.data == "addkw_prompt")
async def cb_addkeyword_prompt(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    pending[callback.from_user.id] = "addkeyword"
    await callback.answer()
    await callback.message.answer("Напиши слово или фразу следующим сообщением.")


@dp.callback_query(F.data.startswith("edit_profile:"))
async def cb_edit_profile(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    field = callback.data.split(":", 1)[1]
    label = PROFILE_LABELS.get(field, field)
    pending[callback.from_user.id] = f"profile_field:{field}"
    await callback.answer()
    fields = get_profile_fields()
    current = fields.get(field, "—")
    await callback.message.answer(
        f"Редактируешь: <b>{label}</b>\n\n"
        f"Сейчас: <i>{current}</i>\n\n"
        "Напиши новое значение следующим сообщением:",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "back")
async def cb_back(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer()
    interval_min = CHECK_INTERVAL // 60
    await callback.message.edit_text(
        f"🤖 <b>Freelance Monitor Bot</b>\n\n"
        f"Мониторю: FL.ru, Kwork, Freelance.ru, Weblancer, Freelancehunt, TG-каналы\n"
        f"Интервал: каждые {interval_min} мин\n"
        f"Ключевых слов: {len(get_keywords())}",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@dp.callback_query()
async def cb_unknown(callback: CallbackQuery):
    if callback.from_user.id != USER_ID:
        return
    await callback.answer("Устаревшая кнопка. Нажми /start чтобы открыть меню заново.", show_alert=True)


# ─── Вспомогательные функции ───────────────────────────────────────────────────

async def show_keywords(message: Message):
    kws = get_keywords()
    kw_list = "\n".join(f"• {kw}" for kw in kws) if kws else "Список пуст."
    await message.answer(
        f"🔑 <b>Ключевые слова ({len(kws)}):</b>\n\n{kw_list}\n\n"
        "Нажми на слово чтобы удалить, или добавь новое кнопкой ниже.",
        reply_markup=keywords_keyboard(),
        parse_mode="HTML",
    )


async def show_channels(message: Message):
    channels = get_channels()
    if channels:
        text = f"📢 <b>Telegram-каналы ({len(channels)}):</b>\n\nНажми на канал чтобы удалить, или добавь новый кнопкой ниже."
    else:
        text = "Каналы не настроены. Добавь первый канал кнопкой ниже."
    await message.answer(text, reply_markup=channels_keyboard(), parse_mode="HTML")


async def show_profile(message: Message):
    f = get_profile_fields()
    text = (
        f"👤 <b>Мой профиль</b>\n\n"
        f"<b>Имя:</b> {f.get('name', '—')}\n"
        f"<b>Роль:</b> {f.get('title', '—')}\n"
        f"<b>Локация:</b> {f.get('location', '—')}\n"
        f"<b>Контакт:</b> {f.get('contact', '—')}\n"
        f"<b>ТЗ-бот:</b> {f.get('tzbot', '—')}\n"
        f"<b>Портфолио:</b> {f.get('portfolio', '—')}\n\n"
        f"<b>Услуги:</b>\n{f.get('services', '—')}\n\n"
        f"<b>Навыки:</b>\n{f.get('skills', '—')}\n\n"
        f"<b>Стиль откликов:</b>\n{f.get('style', '—')}\n\n"
        "Нажми на поле чтобы изменить:"
    )
    await message.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")


# ─── Обработчик текстовых сообщений ───────────────────────────────────────────

@dp.message(F.text)
async def handle_text(message: Message):
    if message.from_user.id != USER_ID:
        return
    if message.text and message.text.startswith("/"):
        return

    action = pending.pop(message.from_user.id, None)
    text = message.text.strip() if message.text else ""

    if action == "addchannel":
        arg = text if text.startswith("@") else "@" + text
        if add_channel(arg):
            await message.answer(f"✅ Канал {arg} добавлен.")
        else:
            await message.answer(f"Канал {arg} уже в списке.")
        await show_channels(message)

    elif action == "addkeyword":
        if add_keyword(text):
            await message.answer(f"✅ Слово «{text}» добавлено.")
        else:
            await message.answer(f"«{text}» уже в списке.")
        await show_keywords(message)

    elif action and action.startswith("profile_field:"):
        field = action.split(":", 1)[1]
        set_profile_field(field, text)
        label = PROFILE_LABELS.get(field, field)
        await message.answer(f"✅ <b>{label}</b> обновлено.", parse_mode="HTML")
        await show_profile(message)

    elif action == "vacancy":
        if not OPENROUTER_API_KEY:
            await message.answer("❌ OPENROUTER_API_KEY не задан в .env — отклики не работают.")
            return
        msg = await message.answer("✍️ Генерирую отклик...")
        try:
            response = await generate_response("Вакансия", text, "Ручной ввод")
            await msg.edit_text(f"✍️ <b>Отклик готов:</b>\n\n{response}", parse_mode="HTML")
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка:\n<code>{e}</code>", parse_mode="HTML")

    else:
        # Неизвестное сообщение — показываем главное меню
        await message.answer("Нажми кнопку ниже или /start", reply_markup=main_keyboard())


# ─── Проверка всех источников ──────────────────────────────────────────────────

async def check_all() -> int:
    log.info("Запускаю проверку всех источников...")

    results = await asyncio.gather(
        flru.fetch(),
        kwork.fetch(),
        tg.fetch(get_channels()),
        freelanceru.fetch(),
        weblancer.fetch(),
        freelancehunt.fetch(),
        return_exceptions=True,
    )

    # Keep the global notification cap, but give every source a fair turn.
    errors = [result for result in results if isinstance(result, Exception)]
    sources = [result for result in results if not isinstance(result, Exception)]
    results = [*errors, round_robin(sources)]

    total_new = 0
    for orders in results:
        if isinstance(orders, Exception):
            log.error(f"Ошибка парсера: {orders}")
            continue
        for order in orders:
            if total_new >= MAX_PER_CYCLE:
                break
            full_text = order.title + " " + order.description
            if len(full_text) < MIN_TEXT_LEN:
                continue
            if is_seen(order.id):
                continue
            if order.url and is_seen_url(order.url):
                mark_seen(order.id, order.source, order.title, order.description, order.url)
                continue
            fp = _make_fingerprint(full_text)
            if is_seen_fingerprint(fp):
                mark_seen(order.id, order.source, order.title, order.description, order.url)
                continue
            mark_seen(order.id, order.source, order.title, order.description, order.url)
            if matches(full_text):
                await send_order(bot, USER_ID, order)
                total_new += 1
                await asyncio.sleep(0.5)

    log.info(f"Готово. Новых подходящих заказов: {total_new}")
    return total_new


# ─── Запуск ────────────────────────────────────────────────────────────────────

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("ОШИБКА: BOT_TOKEN не задан в .env файле!")
        return
    if not USER_ID:
        print("ОШИБКА: USER_ID не задан в .env файле!")
        return
    if not OPENROUTER_API_KEY:
        log.warning("OPENROUTER_API_KEY не задан — функция откликов недоступна")

    await bot.set_my_commands([
        BotCommand(command="start",    description="🏠 Главное меню"),
        BotCommand(command="check",    description="🔍 Проверить сейчас"),
        BotCommand(command="keywords", description="🔑 Ключевые слова"),
        BotCommand(command="channels", description="📢 Каналы"),
        BotCommand(command="profile",  description="👤 Мой профиль"),
    ])

    init_db()
    log.info("База данных инициализирована.")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_all, "interval", seconds=CHECK_INTERVAL, id="check_all")
    scheduler.start()
    log.info(f"Планировщик запущен. Интервал: {CHECK_INTERVAL} сек.")

    await check_all()

    log.info("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
