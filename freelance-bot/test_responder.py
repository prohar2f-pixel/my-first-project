import unittest
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.modules.setdefault("openai", SimpleNamespace(AsyncOpenAI=None))
sys.modules.setdefault("config", SimpleNamespace(OPENROUTER_API_KEY="test-key"))
sys.modules.setdefault("database", SimpleNamespace(get_profile_fields=lambda: {}))

import responder


class GenerateResponseTests(unittest.IsolatedAsyncioTestCase):
    def test_profile_does_not_present_legacy_platforms_as_verified_skills(self):
        unsafe_legacy_profile = {
            "name": "Александр Прохоров",
            "title": "Веб-разработчик",
            "skills": "HTML/CSS/JS, WordPress, Tilda, Figma",
            "portfolio": "https://prohar2f-pixel.github.io/my-first-project/",
            "contact": "@alex_prohar",
        }

        with patch.object(
            responder, "get_profile_fields", return_value=unsafe_legacy_profile
        ):
            profile = responder.build_profile_text()

        self.assertIn("https://aiprohar.ru/", profile)
        self.assertIn("собственным кодом", profile.lower())
        self.assertIn("не подтвержд", profile.lower())
        self.assertNotIn("HTML/CSS/JS, WordPress, Tilda, Figma", profile)

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


if __name__ == "__main__":
    unittest.main()
