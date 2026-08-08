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
        text = re.sub(r"<br\s*/?>", "\n", match.group(1), flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = unescape(text).replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            posts.append((start.group(1), text))
    return posts


def split_vacancies(text: str) -> list[str]:
    """Split TG digest posts without breaking consecutive role hashtags."""
    parts: list[str] = []
    current: list[str] = []
    has_contact = False

    for line in text.splitlines():
        stripped = line.strip()
        starts_role = bool(re.match(r"^#\s*[\wА-Яа-яЁё]", stripped))
        if starts_role and current and has_contact:
            part = "\n".join(current).strip()
            if part:
                parts.append(part)
            current = []
            has_contact = False
        current.append(stripped)
        if "➡️" in stripped or "->" in stripped or "→" in stripped:
            has_contact = True

    tail = "\n".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def orders_from_post(channel_name: str, msg_id: str, text: str) -> list[Order]:
    url = f"https://t.me/{channel_name}/{msg_id}"
    parts = split_vacancies(text)
    return [
        Order(
            id=f"tg_{channel_name}_{msg_id}_{index}",
            title=part.splitlines()[0][:80],
            description=part[:2000],
            url=url,
            source=f"TG @{channel_name}",
        )
        for index, part in enumerate(parts, start=1)
    ]


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
                    orders.extend(orders_from_post(channel_name, msg_id, text))

            except Exception as e:
                log.error(f"[TG] Ошибка чтения {channel_name}: {e}")

    return orders
