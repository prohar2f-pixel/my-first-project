import unittest
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

with patch.dict(
    sys.modules,
    {
        "openai": SimpleNamespace(AsyncOpenAI=None),
        "config": SimpleNamespace(OPENROUTER_API_KEY="test-key"),
    },
):
    import responder


class GenerateResponseTests(unittest.IsolatedAsyncioTestCase):
    def test_profile_does_not_present_legacy_platforms_as_verified_skills(self):
        unsafe_legacy_profile = {
            "name": "Александр Прохоров",
            "title": "Веб-разработчик",
            "skills": "HTML/CSS/JS, WordPress, Tilda, Figma",
            "portfolio": "https://prohar2f-pixel.github.io/my-first-project/",
            "contact": "@unverified_contact",
        }

        with patch.object(
            responder, "get_profile_fields", return_value=unsafe_legacy_profile
        ):
            profile = responder.build_profile_text()

        self.assertIn("https://aiprohar.ru/", profile)
        self.assertIn("собственным кодом", profile.lower())
        self.assertIn("не подтвержд", profile.lower())
        self.assertIn("@alex_prohar", profile)
        self.assertNotIn("@unverified_contact", profile)
        self.assertNotIn("HTML/CSS/JS, WordPress, Tilda, Figma", profile)
        self.assertIn("SALON 01", profile)
        self.assertIn("не клиентская работа", profile)

    async def test_sends_profile_as_system_message(self):
        completion = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Готовый отклик"))]
        )
        create = AsyncMock(return_value=completion)
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with (
            patch.object(responder, "OPENROUTER_API_KEY", "test-key"),
            patch.object(responder, "build_profile_text", return_value="Профиль исполнителя"),
            patch.object(responder, "AsyncOpenAI", return_value=client),
        ):
            result = await responder.generate_response("Заголовок", "Описание", "Источник")

        self.assertEqual(result, "Готовый отклик")
        request = create.await_args.kwargs
        self.assertNotIn("system", request)
        self.assertEqual(request["messages"][0], {
            "role": "system",
            "content": "Профиль исполнителя",
        })
        self.assertEqual(request["messages"][1]["role"], "user")

    async def test_uses_configured_openrouter_model(self):
        completion = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Готовый отклик"))]
        )
        create = AsyncMock(return_value=completion)
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with (
            patch.object(responder, "OPENROUTER_API_KEY", "test-key"),
            patch.object(responder, "OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            patch.object(responder, "build_profile_text", return_value="Профиль"),
            patch.object(responder, "AsyncOpenAI", return_value=client),
        ):
            await responder.generate_response("Заголовок", "Описание", "Источник")

        self.assertEqual(create.await_args.kwargs["model"], "openai/gpt-4o-mini")

    async def test_generate_draft_regenerates_one_invalid_response(self):
        invalid = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="Работаю с Tilda пять лет и гарантирую рост на 40%."
            ))]
        )
        safe = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content=(
                    "Основной опыт у меня в адаптивной разработке собственным кодом. "
                    "Точную оценку дам после просмотра материалов."
                )
            ))]
        )
        create = AsyncMock(side_effect=[invalid, safe])
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with (
            patch.object(responder, "OPENROUTER_API_KEY", "test-key"),
            patch.object(responder, "get_profile_fields", return_value={}),
            patch.object(responder, "AsyncOpenAI", return_value=client),
        ):
            self.assertTrue(
                hasattr(responder, "generate_draft"),
                "Task 3 must implement responder.generate_draft",
            )
            result = await responder.generate_draft(
                "Перенос Tilda", "Нужен перенос сайта, подробности позже.", "Тест"
            )

        self.assertFalse(result.fallback)
        self.assertTrue(result.regenerated)
        self.assertIn("собственным кодом", result.text)
        self.assertEqual(create.await_count, 2)

    async def test_generate_draft_returns_contextual_fallback_after_two_violations(self):
        invalid = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="Сделал много WordPress-сайтов за 7 дней и 25 000 рублей."
            ))]
        )
        create = AsyncMock(side_effect=[invalid, invalid])
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with (
            patch.object(responder, "OPENROUTER_API_KEY", "test-key"),
            patch.object(responder, "get_profile_fields", return_value={}),
            patch.object(responder, "AsyncOpenAI", return_value=client),
        ):
            self.assertTrue(
                hasattr(responder, "generate_draft"),
                "Task 3 must implement responder.generate_draft",
            )
            result = await responder.generate_draft(
                "WordPress-разработчик",
                "Нужен специалист по Elementor, назовите точную цену и срок.",
                "Тест",
            )

        self.assertTrue(result.fallback)
        self.assertTrue(result.regenerated)
        self.assertIn("нет", result.text.lower())
        self.assertIn("подтвержд", result.text.lower())
        self.assertIn("https://aiprohar.ru/", result.text)
        self.assertEqual(create.await_count, 2)


if __name__ == "__main__":
    unittest.main()
