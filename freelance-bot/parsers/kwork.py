import re
import hashlib
import logging
import httpx
from parsers import Order

SOURCE = "Kwork"
CATEGORY_IDS = [11, 17, 41]

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
}


async def fetch() -> list[Order]:
    orders = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True, trust_env=False) as client:
        for cat_id in CATEGORY_IDS:
            try:
                resp = await client.get(f"https://kwork.ru/projects?c={cat_id}")
                if resp.status_code != 200:
                    log.warning(f"[Kwork] cat={cat_id}: статус {resp.status_code}")
                    continue

                titles = re.findall(r'class="wants-card__header-title"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)', resp.text)
                descs = re.findall(r'class="wants-card__description"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
                prices = re.findall(r'class="wants-card__price"[^>]*>([^<]+)', resp.text)

                for i, (url_path, title) in enumerate(titles):
                    url = f"https://kwork.ru{url_path}" if url_path.startswith("/") else url_path
                    order_id = hashlib.md5(url.encode()).hexdigest()
                    desc = re.sub(r"<[^>]+>", "", descs[i]).strip() if i < len(descs) else ""
                    price = prices[i].strip() if i < len(prices) else ""
                    orders.append(Order(
                        id=f"kwork_{order_id}",
                        title=title.strip(),
                        description=desc[:500],
                        url=url,
                        source=SOURCE,
                        price=price,
                    ))

            except Exception as e:
                log.error(f"[Kwork] cat={cat_id} Ошибка: {e}")
    return orders
