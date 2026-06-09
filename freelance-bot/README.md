# Freelance Monitor Bot

Бот мониторит новые заказы на FL.ru, Habr Freelance, Kwork и Telegram-каналах,
и присылает тебе уведомление когда появляется подходящий заказ.

## Быстрый старт

### 1. Установи Python
Скачай Python 3.11+ с https://python.org и установи.

### 2. Установи зависимости
Открой папку `freelance-bot` в терминале и выполни:
```
pip install -r requirements.txt
```

### 3. Настрой .env файл
Скопируй `.env.example` → `.env` и заполни:

- **BOT_TOKEN** — создай бота у @BotFather в Telegram, он даст токен
- **USER_ID** — напиши боту @userinfobot, он покажет твой ID
- **API_ID / API_HASH** — зайди на https://my.telegram.org → "API development tools"
- **TG_CHANNELS** — каналы для мониторинга через запятую (например: @freelance_ru,@toppchallenge)

### 4. Запусти бота
```
python main.py
```

При первом запуске Telegram попросит войти в аккаунт для чтения каналов
(введи номер телефона и код подтверждения — один раз).

## Команды бота

| Команда | Что делает |
|---|---|
| /start | Показывает статус |
| /keywords | Список ключевых слов |
| /channels | Список каналов |
| /check | Проверить прямо сейчас |

## Добавить ключевые слова
Открой `config.py` и добавь слова в список `KEYWORDS`.
