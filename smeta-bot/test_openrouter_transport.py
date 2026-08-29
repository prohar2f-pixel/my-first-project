import os
import unittest
from unittest.mock import patch

import openrouter_transport


class OpenRouterTransportTests(unittest.TestCase):
    def test_missing_proxy_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENROUTER_HTTP_PROXY"):
                openrouter_transport.post("https://openrouter.ai/api/v1/chat/completions")

    def test_non_loopback_proxy_is_rejected(self):
        with patch.dict(os.environ, {"OPENROUTER_HTTP_PROXY": "http://10.0.0.8:10809"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "127.0.0.1"):
                openrouter_transport.post("https://openrouter.ai/api/v1/chat/completions")

    def test_valid_proxy_is_passed_to_httpx(self):
        calls = []

        def fake_post(url, **kwargs):
            calls.append((url, kwargs))
            return "response"

        with patch.dict(
            os.environ,
            {"OPENROUTER_HTTP_PROXY": "http://127.0.0.1:10809"},
            clear=True,
        ):
            response = openrouter_transport.post(
                "https://openrouter.ai/api/v1/chat/completions",
                request=fake_post,
                timeout=10,
            )

        self.assertEqual(response, "response")
        self.assertEqual(calls, [(
            "https://openrouter.ai/api/v1/chat/completions",
            {"timeout": 10, "proxy": "http://127.0.0.1:10809"},
        )])


if __name__ == "__main__":
    unittest.main()
