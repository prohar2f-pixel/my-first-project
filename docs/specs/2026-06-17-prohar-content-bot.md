# @ProharContentBot — Спецификация для разработки

> Версия: 1.0 | Дата: 2026-06-17 | Автор: Александр Прохоров  
> Разработчик: Claude Opus (реализует эту спеку целиком)

---

## 1. Executive Summary

ИИ-агент для Александра Прохорова (веб-разработчик, фриланс), который:
1. Предлагает черновики постов 3 раза в неделю
2. Ждёт одобрения через Telegram-бот
3. Публикует одновременно в Telegram-канал и VK-группу
4. Собирает статистику и показывает что работает

Тон голоса: **дружелюбно и простым языком** — как объясняешь другу за кофе, без умных слов.  
Формула контента: 70% экспертный / 20% за кулисами / 10% продающий.

---

## 2. Критерии успеха (Phase 1)

- Бот предлагает 3 черновика поста в неделю без ручного запроса
- Публикация в Telegram-канал + VK работает с одного нажатия ✅
- Бот не повторяет темы из последних 30 дней
- Бот пишет в стиле Александра (обучен на реальных примерах)
- Аналитика доступна по команде `/stats`
- Бот работает на сервере Jarvis без вмешательства после деплоя

---

## 3. Пользователь

**Единственный пользователь:** Александр Прохоров (`USER_ID` в .env)  
Бот **приватный** — отвечает только на сообщения от этого Telegram ID.  
Первое сообщение бота при старте: *"Этот бот — пример того, что я создаю"*

---

## 4. Архитектура системы

```
┌─────────────────────────────────────────────────────┐
│                   Jarvis (Windows VPS)               │
│                                                       │
│  apscheduler (AsyncIOScheduler + SQLite jobstore)    │
│       │                                               │
│       ▼                                               │
│  ContentAgent                                         │
│  ├── TrendCollector (RSS + Tavily API)               │
│  ├── StyleMemory (Type C: примеры из БД)             │
│  ├── HistoryMemory (Type A: темы 30 дней)            │
│  └── ClaudeAPI (генерация текста)                    │
│       │                                               │
│       ▼                                               │
│  aiogram Bot (FSM)                                    │
│  └── Approval Flow → ✅ / ✏️ / ❌ / 🔄               │
│            │                                          │
│            ▼                                          │
│  Publisher                                            │
│  ├── Telegram Bot API (channel post)                 │
│  └── VK API (wall.post в группу)                    │
│            │                                          │
│            ▼                                          │
│  Analytics Collector (отложенный сбор через 48ч)    │
└─────────────────────────────────────────────────────┘
```

---

## 5. Стек технологий

| Компонент | Решение | Версия |
|-----------|---------|--------|
| Язык | Python | 3.11+ |
| Telegram-фреймворк | aiogram | 3.x |
| ИИ-генерация | Claude API (Anthropic) | claude-opus-4-8 |
| База данных | SQLite + WAL mode | — |
| ORM/драйвер | aiosqlite | — |
| Расписание | apscheduler | AsyncIOScheduler |
| Jobstore | SQLAlchemyJobStore (SQLite) | — |
| Тренды | RSS (feedparser) + Tavily API | — |
| VK | vk_api | — |
| Сервер | Jarvis Windows VPS | — |
| Папка | `C:\Users\Administrator\Documents\Projects\content-bot\` | — |

---

## 6. Структура файлов проекта

```
content-bot/
├── main.py                  # Точка входа: инициализация бота + планировщика
├── config.py                # Загрузка .env, константы
├── database.py              # Инициализация SQLite, WAL mode, все запросы
├── scheduler.py             # Логика расписания, apscheduler jobs
├── agent/
│   ├── content_agent.py     # Оркестратор: тренды → генерация → отправка черновика
│   ├── trend_collector.py   # RSS + Tavily API
│   └── claude_client.py     # Обёртка над Anthropic API
├── bot/
│   ├── handlers.py          # Все обработчики aiogram (FSM states)
│   ├── keyboards.py         # Inline-кнопки для approval flow
│   └── states.py            # FSMContext state definitions
├── publisher/
│   ├── telegram_publisher.py # Публикация в Telegram-канал
│   └── vk_publisher.py      # Публикация в VK группу
├── analytics/
│   └── collector.py         # Сбор статистики через 48ч после поста
├── .env                     # Секреты (не в git)
├── requirements.txt
└── README.md
```

---

## 7. База данных (SQLite, WAL mode)

### Таблицы

```sql
-- Стиль: примеры постов для system prompt
CREATE TABLE style_examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- История тем (дедупликация 30 дней)
CREATE TABLE post_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Черновики
CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    video_script TEXT,
    topic TEXT,
    regenerate_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',  -- pending / approved / rejected / published
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME
);

-- Опубликованные посты
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER REFERENCES drafts(id),
    tg_message_id INTEGER,     -- ID сообщения в Telegram-канале
    vk_post_id INTEGER,        -- ID поста в VK
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Аналитика
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER REFERENCES posts(id),
    tg_views INTEGER DEFAULT 0,
    tg_reactions INTEGER DEFAULT 0,
    vk_views INTEGER DEFAULT 0,
    vk_likes INTEGER DEFAULT 0,
    vk_comments INTEGER DEFAULT 0,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. Обучение стилю

**Проблема:** У Александра нет готовых постов. Примеры будут написаны специально.

**Решение:** Хранить примеры в БД (`style_examples`). При генерации — брать все примеры и вставлять в system prompt.

**Команды для управления:**

```
/add_example — бот просит прислать текст поста, сохраняет в style_examples
/list_examples — показывает все примеры (id + первые 50 символов)
/delete_example <id> — удаляет пример
```

**Минимум для старта:** 5 примеров (оптимум 10-15).

**Формат system prompt для Claude:**

```
Ты — контент-менеджер Александра Прохорова, веб-разработчика и создателя ИИ-агентов.

ГОЛОС И СТИЛЬ:
- Дружелюбно и простым языком — как объясняешь другу за кофе
- Без сложных терминов (или с объяснением)
- Конкретные факты и цифры вместо воды
- Иногда личный опыт или история из работы

ПРИМЕРЫ ПОСТОВ АЛЕКСАНДРА (пиши именно так):
---
[пример 1]
---
[пример 2]
---
...

ФОРМУЛА КОНТЕНТА: 70% экспертный / 20% за кулисами / 10% продающий.
Сейчас пишем: [тип поста по формуле]

ТЕМА: [тема из трендов или предложенная]

Напиши пост (150-300 слов) + сценарий для видео 30-60 секунд.
```

---

## 9. Расписание генерации

**Фиксированные слоты:** вторник / четверг / суббота в **10:00 МСК**

```python
# scheduler.py
scheduler.add_job(
    generate_and_send_draft,
    'cron',
    day_of_week='tue,thu,sat',
    hour=10,
    minute=0,
    timezone='Europe/Moscow',
    jobstore='default'  # SQLite persistent jobstore
)
```

**Важно:** jobstore на SQLite — задачи выживают после перезапуска процесса.

---

## 10. FSM: Approval Flow (полный граф состояний)

```
[Бот отправляет черновик]
        │
        ▼
  State: WAITING_APPROVAL
        │
   ┌────┼────────┬──────────┐
   ▼    ▼        ▼          ▼
  ✅   ✏️       ❌          🔄
  │    │         │           │
  │    ▼         ▼           ▼
  │  State:    [черновик   State:
  │  WAITING_  удалён,     REGENERATING
  │  EDIT_     ничего не   │
  │  COMMENT   публикуется]│
  │    │                    │
  │    │ (пользователь      │ [Claude пишет новый]
  │    │  пишет текст)      │
  │    ▼                    │
  │  [regenerate с          │
  │   edit_comment]         │
  │    │                    │
  │    └──────┐  ┌──────────┘
  │           ▼  ▼
  │     State: WAITING_APPROVAL
  │     (новый черновик, счётчик +1)
  │
  ▼
[publisher.publish()]
[State: IDLE]
```

**Счётчик регенераций:** максимум 3. После 3-й кнопка 🔄 скрывается.

**Сообщение бота при отправке черновика:**
```
📝 Новый черновик готов

[текст поста]

---

🎬 Сценарий видео:
[сценарий]

---
Регенерация: [0/3]

[✅ Опубликовать] [✏️ Изменить] [❌ Отмена] [🔄 Ещё раз]
```

**При нажатии ✏️ — бот отвечает:**
```
Напиши что изменить (например: "сделай короче", "добавь конкретный пример", "измени тон"):
```
Пользователь присылает текст → бот добавляет его как `edit_comment` в запрос к Claude → регенерирует.

---

## 11. Тренды (источники тем)

### RSS-ленты (фиксированный список)

```python
RSS_FEEDS = [
    "https://vc.ru/rss/section/ai",
    "https://habr.com/ru/rss/hubs/artificial_intelligence/posts/",
    "https://tlgrm.ru/channels/@digitalbrief/rss",  # Digital Brief
]
```

**Логика:** брать 5 последних постов из каждой ленты → фильтровать по дате (последние 3 дня) → извлекать заголовок + краткое описание → передавать в Claude как "актуальные тренды".

### Tavily API (резервный)

Если RSS пусты или недоступны — делать поиск через Tavily:  
`query = "искусственный интеллект веб-разработка тренды 2026"`

### Темы вручную

Команда `/suggest_topic [тема]` — Александр сам предлагает тему, бот генерирует черновик немедленно (вне расписания).

---

## 12. Публикация

### Telegram

```python
# Публикация в канал (не в личку)
await bot.send_message(
    chat_id=TELEGRAM_CHANNEL_ID,  # @prohar_channel или числовой ID
    text=post_text,
    parse_mode="HTML"
)
```

### VK

**Тип:** группа (не страница).  
**Токен:** user token с правами `wall`, `offline` (долгоживущий).

```python
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
response = vk.wall.post(
    owner_id=-VK_GROUP_ID,  # минус перед ID группы!
    message=post_text,
    from_group=1
)
```

**Обработка ошибок VK:**
- `Error 5 (user authorization failed)` → токен истёк → **бот присылает алерт Александру**: "VK токен истёк, нужно обновить. Как это сделать: /vk_help"
- `Error 9 (flood control)` → retry через 60 секунд (максимум 3 попытки)

**Обновление токена:** вручную через `/vk_token <новый_токен>` — бот сохраняет в .env.

---

## 13. Аналитика

**Сбор:** через 48 часов после публикации (scheduled job в apscheduler).

**Что собирается:**

| Платформа | Метрики |
|-----------|---------|
| Telegram | views (getChat + getForwardersCount) |
| VK | views, likes, comments (wall.getById) |

**Команды:**

```
/stats — сводная таблица за последние 30 дней
/stats week — за последнюю неделю
```

**Формат вывода `/stats`:**

```
📊 Аналитика за 30 дней

Топ постов по охвату:
1. "Как я автоматизировал..." — 1240 👁️ / 45 ❤️
2. "3 инструмента ИИ..." — 980 👁️ / 32 ❤️

По форматам:
Экспертный: avg 850 👁️
За кулисами: avg 1100 👁️
Продающий: avg 420 👁️

Лучший день: суббота
```

---

## 14. Переменные окружения (.env)

```env
# Telegram
BOT_TOKEN=                    # токен @ProharContentBot
TELEGRAM_CHANNEL_ID=          # ID канала для публикации (числовой или @username)
USER_ID=                      # Telegram ID Александра (единственный admin)

# Claude API
ANTHROPIC_API_KEY=

# VK
VK_TOKEN=                     # user token с правами wall, offline
VK_GROUP_ID=                  # числовой ID группы (без минуса)

# Tavily (резервный поиск трендов)
TAVILY_API_KEY=

# Опционально
LOG_LEVEL=INFO
TZ=Europe/Moscow
```

---

## 15. Обработка ошибок (Error Contract)

| Ситуация | Действие |
|----------|----------|
| Claude API timeout (>30с) | Retry 2 раза с backoff 5с → алерт Александру в личку |
| Claude API rate limit | Retry через 60с → алерт если снова |
| VK токен истёк | Алерт с инструкцией `/vk_help`, публикация только в TG |
| Telegram flood control (429) | Retry через `retry_after` секунд из ответа API |
| RSS недоступны | Fallback на Tavily API |
| Tavily API недоступен | Генерация без трендов (Claude предлагает тему сам) |
| SQLite locked | WAL mode решает 99% случаев; если нет — лог + алерт |
| Jarvis перезагрузился | apscheduler + SQLite jobstore восстанавливает задачи |

---

## 16. Команды бота (полный список)

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие + статус бота |
| `/status` | Следующий пост когда, сколько примеров загружено |
| `/generate` | Сгенерировать черновик прямо сейчас (вне расписания) |
| `/suggest_topic <тема>` | Генерация по конкретной теме |
| `/add_example` | Добавить пример поста для обучения стилю |
| `/list_examples` | Список всех примеров |
| `/delete_example <id>` | Удалить пример |
| `/stats` | Аналитика за 30 дней |
| `/stats week` | Аналитика за 7 дней |
| `/vk_token <токен>` | Обновить VK токен |
| `/vk_help` | Инструкция по получению VK токена |
| `/pause` | Остановить расписание |
| `/resume` | Возобновить расписание |

---

## 17. Требования к запуску (Jarvis)

1. Python 3.11+ установлен
2. `pip install -r requirements.txt`
3. `.env` заполнен всеми токенами
4. Минимум 5 примеров добавлено через `/add_example`
5. Запуск: `python main.py` (или Windows Task Scheduler / NSSM-сервис)
6. Логи: `content-bot.log` в папке проекта

**Не должно пересекаться** с `freelance-bot` и другими ботами — разные папки, разные process-ы, разные BOT_TOKEN.

---

## 18. Что НЕ входит в Phase 1

- Instagram (слишком сложный OAuth, отдельный проект)
- Автоматический анализ конкурентов (отдельный продукт)
- Изображения/обложки к постам (text-only)
- YouTube / Shorts
- Связь пост → заявка в @prohar_tz_bot (Phase 2)
- Несколько пользователей

---

## 19. Открытые вопросы для реализации

1. **TELEGRAM_CHANNEL_ID** — нужен точный ID канала куда публиковать (Александр должен добавить бота в канал как администратора с правом постить)
2. **VK_GROUP_ID** — нужен числовой ID группы
3. **RSS-ленты** — список выше примерный, можно скорректировать перед стартом
4. **Пример-посты** — написать 5-10 постов в своём стиле перед первым запуском (через `/add_example`)
5. **Windows Task Scheduler vs NSSM** — выбрать способ автозапуска на Jarvis

---

## 20. Оценка трудозатрат

| Компонент | Оценка |
|-----------|--------|
| Базовая структура + БД + конфиг | 2-3 ч |
| Style system + /add_example | 1-2 ч |
| Trend collector (RSS + Tavily) | 2 ч |
| Claude client + генерация | 2-3 ч |
| aiogram FSM + approval flow | 3-4 ч |
| Telegram publisher | 1 ч |
| VK publisher + error handling | 2-3 ч |
| apscheduler + расписание | 2 ч |
| Analytics collector | 2-3 ч |
| Тестирование + деплой | 3-4 ч |
| **Итого Phase 1** | **~20-25 ч** |
