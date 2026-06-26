import re
import asyncio
import hashlib
import logging
import urllib.request
import feedparser
from parsers import Order

RSS_URL = "https://www.freelance.ru/projects/?rss=1"
SOURCE = "Freelance.ru"

log = logging.getLogger(__name__)
_no_proxy = urllib.request.ProxyHandler({})


async def fetch() -> list[Order]:
    try:
        feed = await asyncio.to_thread(feedparser.parse, RSS_URL, handlers=[_no_proxy])
        orders = []
        for entry in feed.entries:
            url = entry.get("link", "")
            order_id = hashlib.md5(url.encode()).hexdigest()
            orders.append(Order(
                id=f"freelanceru_{order_id}",
                title=entry.get("title", "Без названия"),
                description=re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip(),
                url=url,
                source=SOURCE,
            ))
        return orders
    except Exception as e:
        log.error(f"[Freelance.ru] Ошибка: {e}")
        return []
