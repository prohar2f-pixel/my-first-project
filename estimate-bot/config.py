"""Configuration and environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is required")

# APIs
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is required")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if not SERPER_API_KEY:
    raise ValueError("SERPER_API_KEY is required")

# Access control
ALLOWED_USER_IDS_STR = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = set(int(uid.strip()) for uid in ALLOWED_USER_IDS_STR.split(",") if uid.strip())

# Defaults
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "Москва")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
SERPER_API_URL = "https://google.serper.dev/search"
