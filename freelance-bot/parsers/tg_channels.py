import re
import logging
from html import unescape
import httpx
from parsers import Order

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def parse_channel_html(page_html: str) -> list[tuple[str, str]]:
    """Return text posts paired with the id from their own message block."""
    posts = []
    starts = list(re.finditer(
        r'<div class="tgme_widget_message\b[^>]*data-post="[^/]+/(\d+)"[^>]*>',
        page_html,
    ))
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(page_html)
        block = page_html[start.start():end]
        match = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            block,
            re.DOTALL,
        )
        if not match:
            continue
        text = re.sub(r"<[^>]+>", "", match.group(1))
        text = re.sub(r"\s+", " ", unescape(text)).strip()
        if text:
            posts.append((start.group(1), text))
    return posts


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

                for msg_id, text in parse_channel_html(resp.text):
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
