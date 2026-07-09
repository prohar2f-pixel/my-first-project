# План разработки: Telegram-бот «Смета: материалы + работы»

**Дата ТЗ:** 03.07.2026  
**Уточнение сценария (09.07.2026):** PDF объекта → расчёт стоимости **материалов и работ** по всем позициям  
**Уточнение (09.07.2026):** отдельный **калькулятор** с **самопроверкой** до выдачи отчёта — арифметика не должна ошибаться  
**Уточнение (10.07.2026):** **новый бот с нуля**, существующий `smeta-bot` **не дорабатываем и не меняем**  
**Исполнитель:** Александр Прохоров  

---

## Context

### Реальный сценарий (уточнён заказчиком)

1. Пользователь присылает **PDF** строительного объекта (ведомость / проект / смета с наименованиями **работ и материалов**).
2. Бот извлекает **все позиции** (работы + материалы, объёмы/единицы, если есть).
3. По каждой позиции ищет **актуальные рыночные цены** в интернете.
4. **Калькулятор (чистый код, не LLM)** считает `кол-во × цена`, подытоги, итог.
5. **Самопроверка** пересчитывает всё вторым проходом; при расхождении — отчёт **не отдаётся**, ошибка в лог.
6. Отдаёт Excel + краткий итог в чат.

### Аудитория и ограничения из ТЗ

- Внутренний инструмент (владелец + 2–3 руководства).
- 1–2 запроса в день → можно «тяжёлый» PDF-пайплайн (минуты, не 5–10 с на весь файл).
- ПДн / БД / монетизация не требуются.
- Источник цен: интернет (строительные сайты, Avito, прайсы, форумы).

### Новый проект (не smeta-bot)

| | |
|--|--|
| **Делаем** | Новый репозиторий/папка, свой токен BotFather, свой деплой |
| **Не делаем** | Правки в `Documents/projects/my-first-project/smeta-bot/` |
| **Имя проекта** | `estimate-bot` (рекомендуется) или `smeta-full-bot` |
| **Путь** | `Documents/projects/my-first-project/estimate-bot/` |

`smeta-bot` остаётся как есть (материалы + поставщики). Новый бот — **смета объекта: материалы + работы + калькулятор**.

**Reuse только идей/паттернов** (копируем подходы, не правим чужой код):

- `python-telegram-bot` + polling, `/region`, `/cancel`
- Serper.dev + OpenRouter (httpx)
- pdfplumber + openpyxl  
Ориентир по стилю: `smeta-bot/main.py`, `audit-bot/bot.py` — **read-only reference**.

### Расхождение с текстом ТЗ

В ТЗ — короткий Q&A. Уточнение — **пакетный расчёт по PDF** + **безошибочная арифметика**.

- **Основной сценарий:** PDF → смета (материалы + работы) → verify → отчёт.
- **Nice-to-have:** текстовый вопрос «сколько стоит …» без PDF.

### Важное разделение «не ошибается»

| Что | Гарантия |
|-----|----------|
| **Арифметика** (qty × price, суммы) | **Да** — `Decimal` + dual-pass verify + unit-тесты. LLM **запрещено** считать. |
| **Рыночные цены** из интернета | **Нет** — это ориентир; confidence в отчёте. Дисклеймер обязателен. |
| **Парсинг PDF** (названия, qty) | Лучшие усилия LLM; qty нормализуются и валидируются кодом. |

---

## Рекомендуемый подход

### Стек

| Компонент | Выбор | Основание |
|-----------|--------|-----------|
| Telegram | `python-telegram-bot` 21.x | паттерн как в других ботах |
| PDF | `pdfplumber` | извлечение текста |
| Поиск | Serper.dev (`gl=ru`, `hl=ru`) | свежие цены RU |
| LLM | OpenRouter: extract позиций / цен | **только структура и цены, без математики** |
| **Калькулятор** | **stdlib `decimal.Decimal`** | деньги без float-ошибок |
| Excel | `openpyxl` (+ формулы `=B*C` как 3-й контроль) | отчёт |
| HTTP | `httpx` | Serper / OpenRouter |
| Тесты | `pytest` | обязательны для calculator |
| Deploy | Railway / VPS, polling | низкая нагрузка |
| БД | не нужна | ТЗ |

### Пайплайн (основной)

```
PDF (проект / ведомость)
        │
        ▼
1. Извлечь текст (pdfplumber)
        │
        ▼
2. LLM: позиции [{ type, name, unit, qty? }, ...]
   → код: normalize qty/unit (только валидные числа)
        │
        ▼
3. Поиск цен (Serper + LLM extract price)
   → код: price = Decimal (отклонить мусор)
        │
        ▼
4. ★ CALCULATOR (Python, не LLM)
   line_sum = qty * unit_price
   sum_materials, sum_works, grand_total
        │
        ▼
5. ★ VERIFY (второй независимый проход)
   пересчёт всех строк и итогов
   assert primary == secondary (до копейки)
   если fail → STOP, отчёт не слать
        │
        ▼
6. Excel (значения из calculator + опц. Excel-формулы)
   + caption в Telegram из тех же Decimal
```

### Модуль `calculator.py` (критичный)

**Принцип: единственный источник истины для сумм.**  
Ни handlers, ни LLM, ни Excel-writer не считают «в уме» — только вызывают calculator.

```python
# Контракт (эскиз)
@dataclass
class LineInput:
    type: Literal["material", "work"]
    name: str
    unit: str | None
    qty: Decimal | None
    unit_price: Decimal | None  # price_typical
    price_min: Decimal | None
    price_max: Decimal | None
    confidence: str

@dataclass
class LineResult:
    ...
    line_sum: Decimal | None      # qty * unit_price или None
    included_in_total: bool       # False если нет qty или price
    skip_reason: str | None

@dataclass  
class EstimateResult:
    lines: list[LineResult]
    total_materials: Decimal
    total_works: Decimal
    grand_total: Decimal
    skipped_count: int
    verified: bool                # True только после verify_ok
```

**Правила расчёта:**

1. Деньги и qty — только `Decimal` (не `float`).
2. Округление: **HALF_UP до 2 знаков** на `line_sum` и итогах (копейки).
3. `line_sum = (qty * unit_price).quantize(...)` **только если** оба заданы и ≥ 0.
4. Отрицательные / NaN / нечисловые → позиция `skipped`, в total не входит, флаг в отчёте.
5. `total_materials` = сумма `line_sum` где `type=material` и `included_in_total`.
6. `total_works` аналогично.
7. `grand_total = total_materials + total_works` (тот же quantize).
8. Диапазоны `qty * price_min/max` — **отдельные** поля (для ориентира), не подменяют `line_sum`.

### Самопроверка `verify_estimate()` (до отчёта)

Второй проход **с нуля**, без переиспользования уже посчитанных `line_sum`:

1. Для каждой строки заново: `qty * unit_price` → compare с `line_sum`.
2. Заново сложить materials / works / grand.
3. Сверить: `grand_total == total_materials + total_works`.
4. Сверить число included/skipped.
5. **Опционально (усиление):** третий проход через `sum()` + `math.fsum` на int-копейках (`int(d * 100)`) — integer-only totals, zero float drift.

```text
если verify FAIL:
  → лог ERROR + детали расхождения
  → пользователю: «Ошибка внутреннего расчёта, отчёт не сформирован. Попробуйте ещё раз / напишите разработчику»
  → Excel НЕ отправлять
если verify OK:
  → estimate.verified = True
  → можно писать Excel и caption
```

**Жёсткое правило в `excel_report.py` и handlers:**

```python
if not estimate.verified:
    raise RuntimeError("Refuse to export unverified estimate")
```

### Excel как дополнительный контроль (рекомендуется)

- В ячейки **записывать** qty, price, **и** `line_sum` из calculator.
- Дополнительно колонка/строка с формулой Excel `=D2*E2` (qty×price) и `=SUM(...)` — пользователь может открыть файл и увидеть совпадение.
- Caption Telegram: **только** строки из `EstimateResult` (не пересчитывать в handler).

### Нормализация входов (до calculator)

| Поле | Код | Отклонить |
|------|-----|-----------|
| qty | `Decimal(str)` / запятая→точка | None, "", "-", текст |
| unit_price | то же | None, 0 с low confidence — политика: 0 не включать без явного флага |
| type | enum material\|work | иное → skip |

LLM может вернуть `"120 м2"` в qty — **парсер кода** вытаскивает число; unit отдельно.

---

### Формат Excel (целевой)

| # | Тип | Наименование | Ед. | Кол-во | Цена ед., ₽ | Сумма, ₽ | Диапазон сумм* | В итоге? | Уверенность | Источник |
|---|-----|--------------|-----|--------|-------------|----------|----------------|----------|-------------|----------|
| 1 | Материал | … | шт | 10 | 150.00 | 1500.00 | … | да | high | link |
| 2 | Работа | Покраска | кв.м | 80 | 300.00 | 24000.00 | … | да | medium | link |

\* `qty×min` – `qty×max` если есть.

Подвал:

- Материалы: X.XX ₽  
- Работы: Y.YY ₽  
- **Всего: Z.ZZ ₽**  
- Проверка: ✓ пересчёт совпал  
- Позиций вне итога: N (нет qty/цены)  
- Регион, дата  

---

## Структура проекта (новый каталог)

**Только новый проект.** `smeta-bot/` не трогаем.

```
Documents/projects/my-first-project/estimate-bot/
├── main.py              # handlers; ЗАПРЕТ локальной арифметики
├── pdf_extract.py       # extract works + materials
├── search.py            # search_material / search_work
├── price_extract.py     # LLM → raw price → Decimal
├── calculator.py        # ★ calc + verify_estimate
├── excel_report.py      # export only if verified
├── catalog.py           # категории работ из ТЗ
├── config.py            # env: tokens, ALLOWED_USER_IDS, region
├── tests/
│   ├── test_calculator.py   # ★ обязательные
│   └── test_verify.py
├── .env.example
├── requirements.txt
├── Procfile
├── runtime.txt
└── README.md
```

Отдельный бот у BotFather (новый `TELEGRAM_TOKEN`), отдельные env на деплое.
---

## Этапы реализации

### Этап 0 — Подготовка (0.5 д)

- Создать папку `estimate-bot/` (пустой scaffold).
- Новый бот у BotFather → `TELEGRAM_TOKEN`.
- Ключи `OPENROUTER_API_KEY`, `SERPER_API_KEY` (можно те же аккаунты, что у других проектов).
- Whitelist `ALLOWED_USER_IDS`, регион по умолчанию Москва.
- **Не** открывать `smeta-bot` на запись.
### Этап 1 — Извлечение PDF (1–1.5 д)

JSON items: `type`, `name`, `unit`, `qty`, `raw`.  
Код-нормализация qty/unit. Прогресс «N материалов, M работ».

### Этап 2 — Поиск цен (1 д)

Serper material/work + LLM extract → **только** Decimal prices в коде.  
Параллель с семафором, `/cancel`.

### Этап 3 — ★ Калькулятор + самопроверка (1 д)  **[новый акцент]**

1. Реализовать `calculate_estimate(lines) -> EstimateResult`.
2. Реализовать `verify_estimate(result) -> EstimateResult` (или bool + details).
3. Покрыть **pytest** (см. Verification).
4. Интегрировать: после цен → calc → verify → только потом Excel.
5. При fail verify — сообщение пользователю, без файла.

### Этап 4 — Excel + caption из EstimateResult (0.5–1 д)

Writer **не считает** заново. Опционально Excel-формулы для ручной сверки.  
Стили confidence, дисклеймер.

### Этап 5 — UX (0.5 д)

`/start`, `/help`, `/region`, `/cancel`, PDF, whitelist.  
В `/start`: «Цены — ориентир рынка; **суммы пересчитываются калькулятором дважды**».

### Этап 6 — Каталог работ (0.5 д)

Категории из ТЗ в system prompt.

### Этап 7 — Деплой и сдача (0.5 д)

Env, README, 2–3 PDF, прогон `pytest`.

---

## Критические файлы (все внутри `estimate-bot/`)

| Файл | Действие |
|------|----------|
| **`calculator.py`** | calc + verify; единственный source of truth |
| **`tests/test_calculator.py`** | edge cases, money rounding |
| `main.py` | оркестрация; без ручной арифметики |
| `pdf_extract.py` | works + materials из PDF |
| `search.py` / `price_extract.py` | dual search material/work |
| `excel_report.py` | только verified EstimateResult |
| `config.py`, `requirements.txt`, `.env.example`, `README.md` | scaffold |

**Вне scope правок:** `smeta-bot/**` — только reference при необходимости.

**Reuse паттернов (идеи, не файлы):** Serper POST, OpenRouter chat, PTB polling, `/region` `/cancel`.
---

## Оценка сроков

| Этап | Дни |
|------|-----|
| 0 Подготовка | 0.5 |
| 1 PDF extract | 1–1.5 |
| 2 Search + prices | 1 |
| **3 Calculator + verify + tests** | **1** |
| 4 Excel | 0.5–1 |
| 5 UX | 0.5 |
| 6 Catalog | 0.5 |
| 7 Deploy | 0.5 |
| **Итого** | **~5.5–7 рабочих дней** |

---

## Риски

| Риск | Митигация |
|------|-----------|
| LLM «посчитал» в ответе | Игнорировать любые sum от LLM; только calculator |
| float в openpyxl | Писать `float(decimal)` только на export; считать в Decimal |
| PDF без qty | line_sum None, не в grand_total, явный счётчик skipped |
| Verify false positive noise | Сравнение Decimal exact после quantize |
| Путаница material/work price | разные queries + type в extract |
| Ожидание «идеальных рыночных цен» | дисклеймер; calculator гарантирует только арифметику |

---

## Out of scope (MVP)

- OCR сканов  
- История смет в БД  
- 1С / ГЭСН/ФЕР  
- «Идеальная» рыночная цена  
- Q&A без PDF (фаза 2)

---

## Verification (приёмка)

### Калькулятор (автотесты — must pass)

- [ ] `10 * 150 = 1500.00`
- [ ] `0.1 + 0.2` style: `Decimal` не даёт float-баг; `3 * 0.1` → корректные копейки
- [ ] qty или price `None` → line_sum None, **не** в total
- [ ] смесь materials/works → раздельные итоги и grand
- [ ] `grand == materials + works`
- [ ] отрицательный qty/price → skip
- [ ] пустой список → totals 0.00, verified после verify
- [ ] **verify** ловит намеренно испорченный line_sum (unit-тест inject bug)
- [ ] округление HALF_UP: `1 * 10.005` → по правилам 2 знаков

### E2E / ручные

1. PDF → Excel: materials + works, ✓ в подвале «проверка пройдена».  
2. Caption totals **==** Excel totals.  
3. Позиция без qty не в grand total.  
4. Покраска (работа) ≠ краска (материал).  
5. `/region`, `/cancel`, whitelist.  
6. Симуляция verify fail (dev) → файл не уходит.

---

## Порядок реализации (execute)

1. Scaffold **`estimate-bot/`** (новый проект; smeta-bot не трогать).  
2. **`calculator.py` + pytest** (TDD; без Telegram).  
3. `pdf_extract` → items.  
4. `search` + `price_extract` → Decimal.  
5. Wire: calc → verify → excel → `main.py`.  
6. UX (start/help/region/cancel/whitelist) + deploy + README.
---

## Продуктовая рекомендация

- **Цены** = рыночный ориентир (интернет).  
- **Суммы** = железобетонный calculator + double-check: «никогда не ошибается в расчётах» в смысле **арифметики и отчёта**, а не угадывания рынка.  
- В отчёте явно: «Расчёт проверен повторным пересчётом ✓».  

Это честно для руководства и закрывает запрос «прикрутить калькулятор, чтобы не ошибался и перепроверял перед готовым отчётом».

---

## Go / No-Go: можно ли разрабатывать?

**Да — MVP достаточно специфицирован, можно стартовать.**

Зафиксированный scope MVP:

1. **Новый проект** `estimate-bot/` (smeta-bot не меняем)  
2. PDF (и текст-список) → позиции material/work  
3. Поиск цен в интернете (Serper + LLM)  
4. **Калькулятор Decimal + verify до отчёта**  
5. Excel + итог в Telegram  
6. Регион, cancel, whitelist, дисклеймер  

Не блокирует старт: OCR, 1С, история, идеальная рыночная цена.
---

## Предложения по улучшению (не в MVP, по приоритету)

Ниже — что **имеет смысл**, но **не раздувает** первый релиз. Внедрять после того, как PDF→Excel→verify стабильно работает на 2–3 реальных файлах.

### P1 — высокий ROI, мало кода (после MVP, 0.5–1 д каждое)

| Улучшение | Зачем | Как |
|-----------|--------|-----|
| **Кэш цен 24–48 ч** (SQLite/JSON) | Одинаковые позиции в сметах не дергают Serper повторно; быстрее и дешевле | Ключ: `type+name+unit+region`; TTL |
| **Редактирование qty/цены в чате** | «В Excel 80 м², у нас 100» — пересчёт без нового поиска | `/set 12 qty 100` → calculator → новый Excel |
| **Два сценария итога: min / typical / max** | Для планирования «оптимист / база / пессимист» | Уже есть min/max в extract; calculator считает 3 grand_total |
| **Лимит позиций + «продолжить»** | PDF на 200 строк не съест API и время | Сначала 50, кнопка «ещё 50» |
| **Краткий HTML/текст-превью** до Excel | Руководство видит итог в телефоне без открытия файла | 10 строк + totals в сообщении |

### P2 — заметная ценность, средняя сложность (1–2 д)

| Улучшение | Зачем |
|-----------|--------|
| **Ручной прайс-лист компании** (CSV/Google Sheet) | Свои расценки на работы перекрывают интернет; calculator тот же |
| **Коэффициент региона / сложности** (1.0 / 1.15 / 1.3) | Быстрая подстройка без нового поиска |
| **Разделение «материалы / работы / итого» + % работ** | Для калькулятора услуг и маржи |
| **Текстовый Q&A** «сколько покрасить 1 м²?» | Из исходного ТЗ; один item → search → ответ |
| **Сравнение двух прогонов** (вчера vs сегодня) | Если появится история файлов |

### P3 — позже / дорого / спорно

| Улучшение | Почему отложить |
|-----------|-----------------|
| OCR сканов | Отдельный пайплайн, качество на кривых PDF |
| Интеграция 1С / ГЭСН-ФЕР | Другой продукт (нормативная смета) |
| Автозакуп / ссылки «купить» | Юр. и UX-сложность |
| Мультиюзер + роли + архив смет | Нужна БД и политика доступа |
| Агентный «глубокий» парсинг сайтов | Хрупко, медленно; Serper-сниппетов хватает для ориентира |

### Что **не** советую улучшать в MVP

- Красивые inline-кнопки на каждую позицию — шум при 50 строках.  
- «Гарантия цены как у подрядчика» — нельзя честно обещать.  
- Сложный UI-мастер вместо PDF — для 1–2 запросов/день PDF быстрее.

### Рекомендуемый порядок после MVP

```
MVP (этот план)
  → P1: кэш + 3 сценария min/typical/max + превью в чате
  → P1: ручная правка qty → пересчёт
  → P2: свой прайс работ компании (если есть)
  → P2: одиночный Q&A по желанию
```

### Один продуктовый штрих в MVP (почти бесплатно)

В Excel и caption уже заложить поля:

- `total_min` / `total_typical` / `total_max` (calculator считает три суммы из price_min/typical/max)

Даже если в первом UI показываем только **typical**, схема данных готова к «вилка для планирования» без переделки calculator.

---

## Итог для решения

| Вопрос | Ответ |
|--------|--------|
| Можно разрабатывать? | **Да** |
| Где код? | **Новый** `estimate-bot/`, **не** smeta-bot |
| Что обязательно в v1? | PDF → цены → **calculator+verify** → Excel |
| Что улучшать сразу после? | Кэш, вилка min/max/typical, правка qty, превью |
| Главный принцип | LLM ищет и структурирует; **код считает и перепроверяет** |
