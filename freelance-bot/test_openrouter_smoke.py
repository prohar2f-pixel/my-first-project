import json
import unittest
from unittest.mock import patch

import smoke_openrouter


class OpenRouterSmokeParsingTests(unittest.TestCase):
    def test_model_catalog_requires_exact_slug(self):
        payload = {"data": [{"id": "anthropic/claude-haiku-4-5"}]}
        self.assertTrue(
            smoke_openrouter.model_is_available(payload, "anthropic/claude-haiku-4-5")
        )
        self.assertFalse(smoke_openrouter.model_is_available(payload, "claude-haiku"))

    def test_completion_summary_uses_reported_model_usage_and_cost(self):
        payload = {
            "model": "anthropic/claude-haiku-4-5",
            "choices": [{"message": {"content": "OK"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6, "cost": 0.00001},
        }
        summary = smoke_openrouter.completion_summary(payload)
        self.assertEqual(summary["model"], "anthropic/claude-haiku-4-5")
        self.assertEqual(summary["total_tokens"], 6)
        self.assertEqual(summary["cost"], 0.00001)

    def test_completion_summary_does_not_invent_missing_cost(self):
        payload = {
            "model": "anthropic/claude-haiku-4-5",
            "choices": [{"message": {"content": "OK"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
        }
        summary = smoke_openrouter.completion_summary(payload)
        self.assertIsNone(summary["cost"])

    def test_invalid_completion_fails_closed(self):
        with self.assertRaises(smoke_openrouter.SmokeError):
            smoke_openrouter.completion_summary({"model": "x", "usage": {}})


class OpenRouterHttpTests(unittest.TestCase):
    def test_http_json_rejects_invalid_json_without_leaking_headers(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"<!doctype html>"
        with patch("smoke_openrouter.urlopen", return_value=response):
            with self.assertRaisesRegex(smoke_openrouter.SmokeError, "invalid JSON"):
                smoke_openrouter.request_json("https://example.test", "secret-key")


if __name__ == "__main__":
    unittest.main()
