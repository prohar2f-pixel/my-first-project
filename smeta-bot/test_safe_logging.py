import logging
import unittest

import safe_logging


class SafeLoggingTests(unittest.TestCase):
    def test_http_clients_do_not_log_secret_bearing_urls_at_info(self):
        logging.getLogger("httpx").setLevel(logging.INFO)
        logging.getLogger("httpcore").setLevel(logging.INFO)

        safe_logging.configure()

        self.assertEqual(logging.getLogger("httpx").level, logging.WARNING)
        self.assertEqual(logging.getLogger("httpcore").level, logging.WARNING)


if __name__ == "__main__":
    unittest.main()
