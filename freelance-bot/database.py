import os
import sqlite3
from pathlib import Path

_data_dir = Path(os.getenv("DATA_DIR", Path(__file__).parent))
DB_PATH = _data_dir / "seen_orders.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                id      TEXT PRIMARY KEY,
                source  TEXT NOT NULL,
                title   TEXT DEFAULT '',
                description TEXT DEFAULT '',
                seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Добавить колонки если их нет (для старых БД)
        try:
            conn.execute("ALTER TABLE seen ADD COLUMN title TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE seen ADD COLUMN description TEXT DEFAULT ''")
        except Exception:
            pass
        conn.execute("DELETE FROM seen WHERE seen_at < datetime('now', '-30 days')")

        conn.execute("CREATE TABLE IF NOT EXISTS channels (name TEXT PRIMARY KEY)")
        conn.execute("CREATE TABLE IF NOT EXISTS keywords (word TEXT PRIMARY KEY)")
        conn.commit()

        # Засеять из config.py при первом запуске — дальше список живёт только в БД
        if conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0] == 0:
            from config import TG_CHANNELS
            conn.executemany("INSERT OR IGNORE INTO channels (name) VALUES (?)", [(c,) for c in TG_CHANNELS])
        if conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0] == 0:
            from config import KEYWORDS
            conn.executemany("INSERT OR IGNORE INTO keywords (word) VALUES (?)", [(k.lower(),) for k in KEYWORDS])
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


def is_seen(order_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM seen WHERE id = ?", (order_id,)).fetchone()
    return row is not None


def mark_seen(order_id: str, source: str, title: str = "", description: str = ""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen (id, source, title, description) VALUES (?, ?, ?, ?)",
            (order_id, source, title[:200], description[:500]),
        )
        conn.commit()


def get_order(order_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, source, title, description FROM seen WHERE id = ?",
            (order_id,)
        ).fetchone()
    if row:
        return {"id": row[0], "source": row[1], "title": row[2], "description": row[3]}
    return None
