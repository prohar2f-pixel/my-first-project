import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "seen_orders.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                id      TEXT PRIMARY KEY,
                source  TEXT NOT NULL,
                seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Удаляем старые записи старше 30 дней, чтобы база не росла бесконечно
        conn.execute("DELETE FROM seen WHERE seen_at < datetime('now', '-30 days')")
        conn.commit()


def is_seen(order_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM seen WHERE id = ?", (order_id,)).fetchone()
    return row is not None


def mark_seen(order_id: str, source: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen (id, source) VALUES (?, ?)",
            (order_id, source),
        )
        conn.commit()
