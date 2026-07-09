# estimate-bot

Telegram-бот для расчёта смет объектов (материалы + работы).

## Что он делает

1. Получает PDF смету или текстовый список позиций
2. Извлекает работы и материалы с объёмами
3. Ищет актуальные рыночные цены в интернете
4. **Калькулятор считает суммы (Decimal, без ошибок)**
5. **Самопроверка пересчитывает всё дважды** — если расхождение → ошибка, файл не отправляется
6. Экспортирует результат в Excel + итог в чат

## Установка

```bash
pip install -r requirements.txt
cp .env.example .env
# Заполнить .env реальными значениями
```

## Конфигурация

- `TELEGRAM_TOKEN` — новый бот от BotFather
- `OPENROUTER_API_KEY` — для LLM (структурирование, парсинг цен)
- `SERPER_API_KEY` — для поиска цен в интернете
- `ALLOWED_USER_IDS` — список юзеров через запятую (Telegram ID)
- `DEFAULT_REGION` — Москва (для поиска цен)

## Разработка

### Тесты

```bash
pytest tests/
```

### Запуск локально

```bash
python main.py
```

## Архитектура

| Файл | Задача |
|------|--------|
| `calculator.py` | ★ Расчёты + двойная проверка (Decimal, verify) |
| `main.py` | Telegram handlers (no arithmetic) |
| `pdf_extract.py` | Извлечение позиций из PDF (pdfplumber + LLM) |
| `search.py` | Поиск цен по материалам/работам (Serper + LLM) |
| `price_extract.py` | Парсинг цен → Decimal |
| `excel_report.py` | Экспорт только if verified |
| `config.py` | Конфиг и env vars |
| `tests/` | pytest: calculator, verify, edge cases |

## Принципы

- **Арифметика** — только код (Decimal), не LLM
- **Самопроверка** — второй независимый проход пересчитывает на копейку
- **Жёсткое правило** — verify fail → Excel не отправляется

## Статус

Этап 0: ✅ Scaffold
Этап 1: PDF extract (в разработке)
Этап 2: Поиск цен
Этап 3: Тесты для calculator
Этап 4: Excel
Этап 5: UX
Этап 6: Каталог
Этап 7: Деплой
