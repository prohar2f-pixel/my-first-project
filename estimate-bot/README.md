# estimate-bot

Telegram-бот для расчёта смет строительных объектов (материалы + работы).

## Что он делает

1. **Загрузишь PDF** → смету, проект, ведомость материалов
2. **Извлекает позиции** → работы и материалы с объёмами (LLM + pdfplumber)
3. **Ищет рыночные цены** → Serper.dev в интернете (по регионам)
4. **Считает суммы** → `Decimal`, без ошибок округления (до копейки)
5. **Самопроверка** → пересчитывает всё вторым проходом независимо
6. **Отчёт** → если проверка OK → Excel + итог в Telegram; если ошибка → сообщение об ошибке

## Установка и запуск

### Требования
- Python 3.11+
- Telegram (новый бот от BotFather)
- API ключи: OpenRouter, Serper.dev

### Шаги

```bash
# 1. Клонировать / открыть проект
cd estimate-bot

# 2. Создать виртуальное окружение (опционально)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env (из .env.example)
cp .env.example .env

# 5. Заполнить .env реальными значениями:
# TELEGRAM_TOKEN=123456:ABCxyzPQR...
# OPENROUTER_API_KEY=sk-...
# SERPER_API_KEY=...
# ALLOWED_USER_IDS=123456789,987654321
# DEFAULT_REGION=Москва

# 6. Запустить бота
python main.py
```

## Конфигурация

| Переменная | Значение | Где получить |
|-----------|----------|--------------|
| `TELEGRAM_TOKEN` | BotFather токен | https://t.me/BotFather |
| `OPENROUTER_API_KEY` | OpenRouter key (GPT-4, Claude) | https://openrouter.ai |
| `SERPER_API_KEY` | Serper.dev key для поиска | https://serper.dev |
| `ALLOWED_USER_IDS` | Твой Telegram ID, через запятую | Напиши боту `/start`, увидишь в логах |
| `DEFAULT_REGION` | Москва (для поиска цен) | Указывается при запуске или коман-дой `/region` |

## Тестирование

### Unit-тесты калькулятора

```bash
pytest tests/ -v
```

Тесты проверяют:
- Парсинг количеств (Decimal из текста, русские форматы)
- Округление (HALF_UP, копейки)
- Расчёты (материалы + работы отдельно)
- Самопроверку (verify ловит ошибки)

### Интеграционное тестирование

1. Создай тестовый PDF с примерной сметой
2. Отправь боту → проверь Extract, Search, Calculate, Excel

## Команды бота

- `/start` — справка + правила
- `/region <название>` — установить регион для поиска цен
- `/cancel` — отменить текущую операцию
- **Отправь PDF** → начнётся обработка

## Архитектура

```
User → Telegram
  ↓ (PDF file)
main.py
  ├→ pdf_extract.py (pdfplumber + OpenRouter)
  │   ↓ [type, name, unit, qty]
  ├→ search.py (Serper.dev + OpenRouter)
  │   ↓ [price_typical, price_min, price_max, confidence]
  ├→ calculator.py ← ЕДИНСТВЕННЫЙ источник истины
  │   ├→ calculate_estimate() (Decimal × Decimal → Decimal)
  │   └→ verify_estimate() (двойная проверка)
  ├→ excel_report.py (только if verified=True)
  │   ↓ [smeta_YYYYMMDD_HHMMSS.xlsx]
  └→ Caption + File → Telegram
```

| Компонент | Задача | Правило |
|-----------|--------|--------|
| **calculator.py** | ★ Все расчёты (Decimal) | Никогда не трогаем вычисления; verify должен пройти |
| **main.py** | Оркестрация (handlers, async) | ЗАПРЕТ на арифметику в обработчиках |
| **pdf_extract.py** | Парсинг PDF → JSON | Вхождение: пусты текст; выход: список позиций |
| **search.py** | Поиск рыночных цен | Вход: name, unit, region; выход: price_data dict |
| **price_extract.py** | Нормализация цен | to_decimal, отклонение 0 и отрицательных |
| **excel_report.py** | Excel export | Проверка: `if not verified: raise RuntimeError` |
| **config.py** | Конфиг (env vars) | Валидация при импорте; fail fast |
| **catalog.py** | Каталог работ/материалов | Ключевые слова для классификации |
| **tests/** | Unit-тесты | Обязательно для calculator.py |

## Принципы и гарантии

### Гарантированные
- ✅ **Арифметика** — Decimal-only, LLM это **не трогает**
- ✅ **Самопроверка** — verify пересчитывает всё независимо
- ✅ **No-export-if-fail** — `if not verified: raise RuntimeError`
- ✅ **Точность** — до копейки (2 знака, HALF_UP)

### НЕ гарантированные
- ⚠️ **Рыночные цены** — это ориентир (Serper + интернет)
- ⚠️ **Парсинг PDF** — зависит от качества OCR и формата

## Статус разработки

| Этап | Задача | Статус |
|------|--------|--------|
| 0 | Scaffold (config, requirements, README) | ✅ Done |
| 1 | PDF extract (pdfplumber + LLM) | ✅ Done (не протестировано) |
| 2 | Search prices (Serper + LLM) | ✅ Done (не протестировано) |
| 3 | Calculator + verify + tests | ✅ Done (12 tests ✅) |
| 4 | Excel export | ✅ Done (не протестировано) |
| 5 | Telegram handlers + UX | ✅ Done (не протестировано) |
| 6 | Catalog of works | ✅ Done |
| 7 | Deploy (Railway / VPS) | ⏳ Ready for deploy |

## Интеграционное тестирование (TODO)

Нужны API ключи и реальный PDF для полного теста:
1. Загрузить PDF в бот
2. Проверить Extract: выведет ли позиции?
3. Проверить Search: найдёт ли цены?
4. Проверить Calculate: считает ли правильно?
5. Проверить Verify: ловит ли ошибки?
6. Проверить Excel: форматирует ли правильно?
