import re
import logging
import httpx
from parsers import Order

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


async def fetch(channels: list[str]) -> list[Order]:
    if not channels:
        return []

    orders = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, trust_env=False) as client:
        for channel in channels:
            channel_name = channel.strip().lstrip("@")
            try:
                resp = await client.get(f"https://t.me/s/{channel_name}")
                if resp.status_code != 200:
                    log.warning(f"[TG] {channel_name}: статус {resp.status_code}")
                    continue

                messages = re.findall(
                    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
                    resp.text, re.DOTALL
                )
                ids = re.findall(
                    r'data-post="[^/]+/(\d+)"',
                    resp.text
                )

                for i, (msg_html, msg_id) in enumerate(zip(messages, ids)):
                    text = re.sub(r"<[^>]+>", "", msg_html).strip()
                    text = re.sub(r"\s+", " ", text)
                    if not text:
                        continue
                    url = f"https://t.me/{channel_name}/{msg_id}"
                    orders.append(Order(
                        id=f"tg_{channel_name}_{msg_id}",
                        title=text[:80].replace("\n", " "),
                        description=text[:500],
                        url=url,
                        source=f"TG @{channel_name}",
                    ))

            except Exception as e:
                log.error(f"[TG] Ошибка чтения {channel_name}: {e}")

    return orders
