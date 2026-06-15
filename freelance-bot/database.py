import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "seen_orders.db"


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
        conn.commit()


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
