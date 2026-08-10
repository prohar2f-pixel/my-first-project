import importlib
import importlib.util
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import patch

from response_policy import DraftResult


def load_formatting():
    if importlib.util.find_spec("draft_formatting") is None:
        raise AssertionError(
            "draft_formatting.py is missing; Task 4 must implement it"
        )
    return importlib.import_module("draft_formatting")


class _Route:
    def __call__(self, *args, **kwargs):
        del args, kwargs
        return lambda handler: handler


class _Dispatcher:
    def __init__(self):
        self.message = _Route()
        self.callback_query = _Route()


class _Field:
    def __eq__(self, other):
        del other
        return self

    def startswith(self, prefix):
        del prefix
        return self


def load_main():
    if "main" in sys.modules:
        return sys.modules["main"]

    aiogram = SimpleNamespace(
        Bot=lambda **kwargs: SimpleNamespace(),
        Dispatcher=_Dispatcher,
        F=SimpleNamespace(data=_Field(), text=_Field()),
    )
    aiogram_filters = SimpleNamespace(Command=lambda *args, **kwargs: object())
    aiogram_types = SimpleNamespace(
        Message=object,
        CallbackQuery=object,
        InlineKeyboardMarkup=lambda **kwargs: SimpleNamespace(**kwargs),
        InlineKeyboardButton=lambda **kwargs: SimpleNamespace(**kwargs),
        BotCommand=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    database = SimpleNamespace(
        init_db=lambda: None,
        is_seen=lambda *_: False,
        is_seen_fingerprint=lambda *_: False,
        is_seen_url=lambda *_: False,
        mark_seen=lambda *_: None,
        get_order=lambda *_: None,
        get_channels=lambda: [],
        add_channel=lambda *_: True,
        remove_channel=lambda *_: True,
        get_keywords=lambda: [],
        add_keyword=lambda *_: True,
        remove_keyword=lambda *_: True,
        get_profile_fields=lambda: {},
        set_profile_field=lambda *_: None,
        get_stats_by_source=lambda: [],
        _make_fingerprint=lambda value: value,
    )
    modules = {
        "aiogram": aiogram,
        "aiogram.filters": aiogram_filters,
        "aiogram.types": aiogram_types,
        "apscheduler": SimpleNamespace(),
        "apscheduler.schedulers": SimpleNamespace(),
        "apscheduler.schedulers.asyncio": SimpleNamespace(
            AsyncIOScheduler=lambda: SimpleNamespace()
        ),
        "config": SimpleNamespace(
            BOT_TOKEN="test-token",
            USER_ID=100,
            CHECK_INTERVAL=60,
            OPENROUTER_API_KEY="test-key",
        ),
        "database": database,
        "filters": SimpleNamespace(matches=lambda *_: True),
        "notifier": SimpleNamespace(send_order=AsyncMock()),
        "openai": SimpleNamespace(AsyncOpenAI=None),
        "selection": SimpleNamespace(round_robin=lambda sources: iter(sources)),
    }
    for name in (
        "flru",
        "kwork",
        "tg_channels",
        "freelanceru",
        "weblancer",
        "freelancehunt",
    ):
        modules[f"parsers.{name}"] = SimpleNamespace(fetch=AsyncMock())

    with patch.dict(sys.modules, modules):
        loaded = importlib.import_module("main")
    sys.modules.pop("responder", None)
    return loaded


class DraftMessageFormattingTests(unittest.TestCase):
    def test_formats_text_risks_and_manual_send_notice(self):
        formatting = load_formatting()
        result = DraftResult(
            text="Готов сверстать <b>сайт</b>.",
            warnings=(
                "unverified_platform:wordpress",
                "missing_scope:layouts",
                "missing_scope:unique_pages",
                "missing_scope:integrations",
                "exact_estimate:unsafe",
            ),
            regenerated=True,
            fallback=True,
        )

        message = formatting.format_draft_message(result)

        self.assertIn("<b>Черновик отклика</b>", message)
        self.assertIn("Готов сверстать &lt;b&gt;сайт&lt;/b&gt;.", message)
        self.assertIn("<b>Проверить перед отправкой</b>", message)
        self.assertIn("WordPress", message)
        self.assertIn("макеты", message.lower())
        self.assertIn("уникальных страниц", message.lower())
        self.assertIn("формы и интеграции", message.lower())
        self.assertIn("цену и срок", message.lower())
        self.assertIn("безопасный шаблон", message.lower())
        self.assertIn("не отправлен заказчику", message.lower())

    def test_keeps_verification_block_when_no_risks_were_detected(self):
        formatting = load_formatting()

        message = formatting.format_draft_message(
            DraftResult(text="Честный готовый текст.")
        )

        self.assertIn("<b>Проверить перед отправкой</b>", message)
        self.assertIn("автоматических предупреждений нет", message.lower())
        self.assertIn("не отправлен заказчику", message.lower())

    def test_generation_error_does_not_expose_rejected_text(self):
        formatting = load_formatting()
        self.assertTrue(
            hasattr(formatting, "format_generation_error"),
            "Task 4 must hide rejected text in generation errors",
        )

        message = formatting.format_generation_error(
            ValueError("Отклонённый <b>опасный текст</b>")
        )

        self.assertIn("Не удалось подготовить безопасный черновик", message)
        self.assertIn("уточните факты", message.lower())
        self.assertNotIn("опасный текст", message)


class DraftGenerationFormattingTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_formatted_draft_returns_checked_message(self):
        formatting = load_formatting()
        generator = AsyncMock(
            return_value=DraftResult(
                text="Основной опыт - собственный код.",
                warnings=("unverified_platform:tilda",),
            )
        )

        message = await formatting.generate_formatted_draft(
            "Перенос сайта",
            "Нужна работа в Tilda",
            "Ручной ввод",
            generator=generator,
        )

        self.assertIn("Основной опыт - собственный код.", message)
        self.assertIn("Tilda", message)
        self.assertIn("не отправлен заказчику", message.lower())
        generator.assert_awaited_once_with(
            "Перенос сайта",
            "Нужна работа в Tilda",
            "Ручной ввод",
        )


class TelegramDraftPathTests(unittest.IsolatedAsyncioTestCase):
    async def test_found_order_path_uses_checked_draft_message(self):
        main = load_main()
        self.assertTrue(
            hasattr(main, "generate_formatted_draft"),
            "Task 4 must use generate_formatted_draft in Telegram handlers",
        )
        progress = SimpleNamespace(edit_text=AsyncMock())
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=100),
            data="reply:order-1",
            answer=AsyncMock(),
            message=SimpleNamespace(answer=AsyncMock(return_value=progress)),
        )
        order = {
            "title": "Перенос сайта",
            "description": "Нужна Tilda",
            "source": "Канал",
        }

        with (
            patch.object(main, "get_order", return_value=order),
            patch.object(
                main,
                "generate_formatted_draft",
                AsyncMock(return_value="<b>Черновик отклика</b>"),
            ) as generate,
        ):
            await main.cb_reply(callback)

        generate.assert_awaited_once_with(
            "Перенос сайта",
            "Нужна Tilda",
            "Канал",
            generator=main.generate_draft,
        )
        progress.edit_text.assert_awaited_once_with(
            "<b>Черновик отклика</b>",
            parse_mode="HTML",
        )

    async def test_manual_vacancy_path_uses_checked_draft_message(self):
        main = load_main()
        self.assertTrue(
            hasattr(main, "generate_formatted_draft"),
            "Task 4 must use generate_formatted_draft in Telegram handlers",
        )
        progress = SimpleNamespace(edit_text=AsyncMock())
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=100),
            text="Текст вакансии",
            answer=AsyncMock(return_value=progress),
        )
        main.pending[100] = "vacancy"

        with patch.object(
            main,
            "generate_formatted_draft",
            AsyncMock(return_value="<b>Черновик отклика</b>"),
        ) as generate:
            await main.handle_text(message)

        generate.assert_awaited_once_with(
            "Вакансия",
            "Текст вакансии",
            "Ручной ввод",
            generator=main.generate_draft,
        )
        progress.edit_text.assert_awaited_once_with(
            "<b>Черновик отклика</b>",
            parse_mode="HTML",
        )


if __name__ == "__main__":
    unittest.main()
