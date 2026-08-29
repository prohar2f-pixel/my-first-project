import os
import unittest
from unittest.mock import patch

import openrouter_client


class OpenRouterClientTests(unittest.TestCase):
    def test_missing_proxy_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENROUTER_HTTP_PROXY"):
                openrouter_client.create_async_client(client_factory=lambda **kwargs: kwargs)

    def test_non_loopback_proxy_is_rejected(self):
        with patch.dict(os.environ, {"OPENROUTER_HTTP_PROXY": "http://192.168.1.9:10809"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "127.0.0.1"):
                openrouter_client.create_async_client(client_factory=lambda **kwargs: kwargs)

    def test_valid_proxy_is_given_to_async_client(self):
        with patch.dict(os.environ, {"OPENROUTER_HTTP_PROXY": "http://127.0.0.1:10809"}, clear=True):
            created = openrouter_client.create_async_client(client_factory=lambda **kwargs: kwargs)

        self.assertEqual(created, {"proxy": "http://127.0.0.1:10809"})


if __name__ == "__main__":
    unittest.main()
