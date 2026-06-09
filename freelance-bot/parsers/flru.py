import hashlib
import logging
import feedparser
from parsers import Order

RSS_URL = "https://www.fl.ru/rss/all.xml"
SOURCE = "FL.ru"

log = logging.getLogger(__name__)


async def fetch() -> list[Order]:
    try:
        feed = feedparser.parse(RSS_URL)
        orders = []
        for entry in feed.entries:
            url = entry.get("link", "")
            order_id = hashlib.md5(url.encode()).hexdigest()
            orders.append(Order(
                id=f"flru_{order_id}",
                title=entry.get("title", "Без названия"),
                description=_clean(entry.get("summary", "")),
                url=url,
                source=SOURCE,
            ))
        return orders
    except Exception as e:
        log.error(f"[FL.ru] Ошибка: {e}")
        return []


def _clean(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text).strip()
