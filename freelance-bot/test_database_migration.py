import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import database


LEGACY_SKILLS = (
    "HTML/CSS/JS верстка (без фреймворков), адаптивный дизайн, "
    "WordPress, Tilda, GitHub Pages, Cloudflare Workers. "
    "Python (Telegram-боты: aiogram, python-telegram-bot, Telethon). "
    "Anthropic Claude API, OpenAI API \u2014 ИИ-интеграции и автоматизация. "
    "Figma \u2014 работа по макетам."
)
LEGACY_PORTFOLIO = "https://prohar2f-pixel.github.io/my-first-project/"


def create_profile_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE profile (key TEXT PRIMARY KEY, value TEXT DEFAULT '')"
    )
    conn.executemany(
        "INSERT INTO profile (key, value) VALUES (?, ?)",
        (("skills", LEGACY_SKILLS), ("portfolio", LEGACY_PORTFOLIO)),
    )
    conn.commit()


def migrate(conn: sqlite3.Connection) -> None:
    if not hasattr(database, "migrate_profile"):
        raise AssertionError(
            "database.migrate_profile is missing; Task 3 must implement it"
        )
    database.migrate_profile(conn)


class ProfileMigrationTests(unittest.TestCase):
    def test_migration_replaces_only_known_legacy_defaults(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        create_profile_table(conn)

        migrate(conn)

        fields = dict(conn.execute("SELECT key, value FROM profile"))
        self.assertIn("собственным кодом", fields["skills"].lower())
        self.assertNotIn("WordPress", fields["skills"])
        self.assertNotIn("Tilda", fields["skills"])
        self.assertEqual(fields["portfolio"], "https://aiprohar.ru/")
        version = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'profile_schema_version'"
        ).fetchone()[0]
        self.assertEqual(version, "2")

    def test_migration_preserves_manually_edited_values(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        conn.execute(
            "CREATE TABLE profile (key TEXT PRIMARY KEY, value TEXT DEFAULT '')"
        )
        conn.executemany(
            "INSERT INTO profile (key, value) VALUES (?, ?)",
            (
                ("skills", "Мой вручную проверенный набор навыков"),
                ("portfolio", "https://portfolio.example/custom"),
            ),
        )
        conn.commit()

        migrate(conn)

        fields = dict(conn.execute("SELECT key, value FROM profile"))
        self.assertEqual(fields["skills"], "Мой вручную проверенный набор навыков")
        self.assertEqual(fields["portfolio"], "https://portfolio.example/custom")

    def test_migration_is_idempotent(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        create_profile_table(conn)

        migrate(conn)
        first = conn.execute(
            "SELECT key, value FROM profile ORDER BY key"
        ).fetchall()
        migrate(conn)
        second = conn.execute(
            "SELECT key, value FROM profile ORDER BY key"
        ).fetchall()

        self.assertEqual(second, first)

    def test_migration_rolls_back_all_changes_on_failure(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        create_profile_table(conn)
        conn.execute(
            """
            CREATE TRIGGER reject_portfolio_update
            BEFORE UPDATE OF value ON profile
            WHEN OLD.key = 'portfolio'
            BEGIN
                SELECT RAISE(ABORT, 'portfolio locked');
            END
            """
        )
        conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            migrate(conn)

        fields = dict(conn.execute("SELECT key, value FROM profile"))
        self.assertEqual(fields["skills"], LEGACY_SKILLS)
        self.assertEqual(fields["portfolio"], LEGACY_PORTFOLIO)
        meta_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'app_meta'"
        ).fetchone()
        if meta_exists:
            version = conn.execute(
                "SELECT value FROM app_meta WHERE key = 'profile_schema_version'"
            ).fetchone()
            self.assertIsNone(version)

    def test_init_db_applies_safe_profile_before_first_read(self):
        test_dir = Path(__file__).parent
        with tempfile.TemporaryDirectory(dir=test_dir) as temp_dir:
            db_path = Path(temp_dir) / "seen_orders.db"
            fake_config = SimpleNamespace(TG_CHANNELS=[], KEYWORDS=[])
            with (
                patch.object(database, "DB_PATH", db_path),
                patch.dict(sys.modules, {"config": fake_config}),
            ):
                database.init_db()

            with sqlite3.connect(db_path) as conn:
                fields = dict(conn.execute("SELECT key, value FROM profile"))
                meta_exists = conn.execute(
                    "SELECT 1 FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'app_meta'"
                ).fetchone()
                self.assertIsNotNone(
                    meta_exists,
                    "init_db must create app_meta and run the profile migration",
                )
                version = conn.execute(
                    "SELECT value FROM app_meta WHERE key = 'profile_schema_version'"
                ).fetchone()[0]

        self.assertEqual(fields["portfolio"], "https://aiprohar.ru/")
        self.assertNotIn("Tilda", fields["skills"])
        self.assertNotIn("WordPress", fields["skills"])
        self.assertEqual(version, "2")


if __name__ == "__main__":
    unittest.main()
