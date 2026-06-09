import logging
from parsers import Order

log = logging.getLogger(__name__)


async def fetch(channels: list[str]) -> list[Order]:
    """
    Читает последние 30 сообщений из каждого Telegram-канала через Telethon.
    Требует API_ID и API_HASH из my.telegram.org.
    При первом запуске попросит войти в аккаунт (один раз).
    """
    if not channels:
        return []

    try:
        from telethon import TelegramClient
        from telethon.errors import FloodWaitError
        from config import API_ID, API_HASH
    except ImportError:
        log.warning("[TG] telethon не установлен, пропускаю.")
        return []

    if not API_ID or not API_HASH:
        log.warning("[TG] API_ID/API_HASH не заданы в .env, пропускаю.")
        return []

    orders = []
    client = TelegramClient("freelance_session", API_ID, API_HASH)

    try:
        await client.start()
        for channel in channels:
            channel = channel.strip()
            if not channel:
                continue
            try:
                async for msg in client.iter_messages(channel, limit=30):
                    if not msg.text:
                        continue
                    channel_name = channel.lstrip("@")
                    url = f"https://t.me/{channel_name}/{msg.id}"
                    orders.append(Order(
                        id=f"tg_{channel_name}_{msg.id}",
                        title=msg.text[:80].replace("\n", " "),
                        description=msg.text[:500],
                        url=url,
                        source=f"TG @{channel_name}",
                    ))
            except FloodWaitError as e:
                log.warning(f"[TG] FloodWait {e.seconds}с для {channel}")
            except Exception as e:
                log.error(f"[TG] Ошибка чтения {channel}: {e}")
    finally:
        await client.disconnect()

    return orders
