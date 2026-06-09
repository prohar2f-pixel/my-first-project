import hashlib
import logging
import httpx
from parsers import Order

SOURCE = "Kwork"
# Категории: 11=сайты, 17=боты/скрипты, 41=интернет-магазины
CATEGORY_IDS = [11, 17, 41]
API_URL = "https://api.kwork.ru/projects"

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


async def fetch() -> list[Order]:
    orders = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        for cat_id in CATEGORY_IDS:
            try:
                resp = await client.get(
                    API_URL,
                    params={"categories": cat_id, "page": 1},
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for item in data.get("response", {}).get("projects", []):
                    url = f"https://kwork.ru/projects/{item['id']}/view"
                    order_id = hashlib.md5(url.encode()).hexdigest()
                    price = item.get("price", "")
                    orders.append(Order(
                        id=f"kwork_{order_id}",
                        title=item.get("name", "Без названия"),
                        description=item.get("description", "")[:500],
                        url=url,
                        source=SOURCE,
                        price=f"{price} ₽" if price else "",
                    ))
            except Exception as e:
                log.error(f"[Kwork] cat={cat_id} Ошибка: {e}")
    return orders
