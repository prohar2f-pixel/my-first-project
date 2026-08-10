import os
import sqlite3
from pathlib import Path

_data_dir = Path(os.getenv("DATA_DIR", Path(__file__).parent))
DB_PATH = _data_dir / "seen_orders.db"

PROFILE_SCHEMA_VERSION = 2
LEGACY_PROFILE_SKILLS = (
    "HTML/CSS/JS верстка (без фреймворков), адаптивный дизайн, "
    "WordPress, Tilda, GitHub Pages, Cloudflare Workers. "
    "Python (Telegram-боты: aiogram, python-telegram-bot, Telethon). "
    "Anthropic Claude API, OpenAI API \u2014 ИИ-интеграции и автоматизация. "
    "Figma \u2014 работа по макетам."
)
LEGACY_PROFILE_PORTFOLIO = "https://prohar2f-pixel.github.io/my-first-project/"
SAFE_PROFILE_SKILLS = (
    "Адаптивные сайты собственным кодом: HTML, CSS и JavaScript. "
    "Работа по макетам Figma. Telegram-боты и AI-интеграции."
)
SAFE_PROFILE_PORTFOLIO = "https://aiprohar.ru/"


def migrate_profile(conn: sqlite3.Connection) -> None:
    """Apply the safe profile migration atomically and preserve custom values."""
    savepoint = "profile_schema_migration"
    conn.execute(f"SAVEPOINT {savepoint}")
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS app_meta ("
            "key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'profile_schema_version'"
        ).fetchone()
        current_version = int(row[0]) if row else 0

        if current_version < PROFILE_SCHEMA_VERSION:
            conn.execute(
                "UPDATE profile SET value = ? WHERE key = 'skills' AND value = ?",
                (SAFE_PROFILE_SKILLS, LEGACY_PROFILE_SKILLS),
            )
            conn.execute(
                "UPDATE profile SET value = ? WHERE key = 'portfolio' AND value = ?",
                (SAFE_PROFILE_PORTFOLIO, LEGACY_PROFILE_PORTFOLIO),
            )
            conn.execute(
                "INSERT INTO app_meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                ("profile_schema_version", str(PROFILE_SCHEMA_VERSION)),
            )

        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
    except Exception:
        conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        raise


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                id          TEXT PRIMARY KEY,
                source      TEXT NOT NULL,
                title       TEXT DEFAULT '',
                description TEXT DEFAULT '',
                fingerprint TEXT DEFAULT '',
                seen_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Добавить колонки если их нет (для старых БД)
        for col in ("title TEXT DEFAULT ''", "description TEXT DEFAULT ''",
                    "fingerprint TEXT DEFAULT ''", "url TEXT DEFAULT ''"):
            try:
                conn.execute(f"ALTER TABLE seen ADD COLUMN {col}")
            except Exception:
                pass
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fingerprint ON seen(fingerprint)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON seen(url)")
        conn.execute("DELETE FROM seen WHERE seen_at < datetime('now', '-30 days')")

        conn.execute("CREATE TABLE IF NOT EXISTS channels (name TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE IF NOT EXISTS keywords (word TEXT PRIMARY KEY)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                key   TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            )
        """)
        conn.commit()

        # Засеять из config.py при первом запуске - дальше список живёт только в БД
        if conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0] == 0:
            from config import TG_CHANNELS
            conn.executemany("INSERT OR IGNORE INTO channels (name) VALUES (?)", [(c,) for c in TG_CHANNELS])
        if conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0] == 0:
            from config import KEYWORDS
            conn.executemany("INSERT OR IGNORE INTO keywords (word) VALUES (?)", [(k.lower(),) for k in KEYWORDS])
        if conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 0:
            defaults = [
                ("name",      "Александр Прохоров"),
                ("location",  "Латвия"),
                ("contact",   "@alex_prohar"),
                ("tzbot",     "@prohar_tz_bot"),
                ("portfolio", SAFE_PROFILE_PORTFOLIO),
                ("services",  (
                    "Сайт-визитка - от 30 000 ₽, 5-7 дней (1-3 страницы, уникальный дизайн, адаптив). "
                    "Лендинг - от 50 000 ₽, 7-14 дней (продающая страница, акцент на конверсию). "
                    "Корпоративный сайт - от 90 000 ₽, 14-30 дней (несколько разделов, каталог, SEO). "
                    "Интернет-магазин - от 150 000 ₽, от 30 дней (каталог, корзина, оплата). "
                    "Telegram-бот - от 25 000 ₽ (автоматизация продаж, поддержки, сбора заявок). "
                    "ИИ-интеграция - от 20 000 ₽ (ИИ-чат, автогенерация контента, анализ данных). "
                    "AEO-оптимизация - от 5 000 ₽, 1-2 дня (настройка сайта для ИИ-поисковиков: ChatGPT, Perplexity, Claude)."
                )),
                ("title",     "Веб-разработчик и специалист по нейросетям"),
                ("skills", SAFE_PROFILE_SKILLS),
                ("style",     (
                    "Коротко, по делу, без воды и шаблонных фраз типа 'готов рассмотреть'. "
                    "Сразу показываю что понял задачу и что конкретно могу сделать. "
                    "Называю цену и сроки если могу оценить по описанию."
                )),
            ]
            conn.executemany("INSERT OR IGNORE INTO profile (key, value) VALUES (?, ?)", defaults)
        migrate_profile(conn)
        conn.commit()


def get_channels() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        return [r[0] for r in conn.execute("SELECT name FROM channels ORDER BY name").fetchall()]


def add_channel(name: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("INSERT OR IGNORE INTO channels (name) VALUES (?)", (name,))
        conn.commit()
        return cur.rowcount > 0


def remove_channel(name: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM channels WHERE name = ?", (name,))
        conn.commit()
        return cur.rowcount > 0


def get_keywords() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        return [r[0] for r in conn.execute("SELECT word FROM keywords ORDER BY word").fetchall()]


def add_keyword(word: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("INSERT OR IGNORE INTO keywords (word) VALUES (?)", (word.lower(),))
        conn.commit()
        return cur.rowcount > 0


def remove_keyword(word: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM keywords WHERE word = ?", (word.lower(),))
        conn.commit()
        return cur.rowcount > 0


import re as _re
import hashlib as _hashlib


def _make_fingerprint(text: str) -> str:
    """MD5 hash of full normalized text - catches exact duplicates across channels."""
    clean = _re.sub(r'[^а-яёa-z0-9\s]', '', text.lower())
    clean = _re.sub(r'\s+', ' ', clean).strip()
    return _hashlib.md5(clean.encode()).hexdigest()


def is_seen(order_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM seen WHERE id = ?", (order_id,)).fetchone()
    return row is not None


def is_seen_fingerprint(fingerprint: str) -> bool:
    if not fingerprint:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM seen WHERE fingerprint = ?", (fingerprint,)
        ).fetchone()
    return row is not None


def is_seen_url(url: str) -> bool:
    if not url:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM seen WHERE url = ?", (url,)).fetchone()
    return row is not None


def mark_seen(order_id: str, source: str, title: str = "", description: str = "", url: str = ""):
    fp = _make_fingerprint(title + " " + description)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen (id, source, title, description, fingerprint, url) VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, source, title[:200], description[:500], fp, url),
        )
        conn.commit()


def get_profile_fields() -> dict[str, str]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT key, value FROM profile").fetchall()
        return {r[0]: r[1] for r in rows}


def set_profile_field(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO profile (key, value) VALUES (?, ?)", (key, value))
        conn.commit()


def get_stats_by_source() -> list[tuple[str, int]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM seen GROUP BY source ORDER BY cnt DESC"
        ).fetchall()
    return rows


def get_order(order_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, source, title, description FROM seen WHERE id = ?",
            (order_id,)
        ).fetchone()
    if row:
        return {"id": row[0], "source": row[1], "title": row[2], "description": row[3]}
    return None
