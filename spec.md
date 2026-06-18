# Спецификация: ИИ-агент для ведения соцсетей

**Версия:** 1.0  
**Дата:** 2026-06-17  
**Разработчик:** Claude Opus 4.8  
**Владелец:** Удача (фрилансер, веб-разработчик)

---

## Краткое описание

Telegram-бот с AI-агентом, который самостоятельно ведёт соцсети фрилансера-разработчика. Агент учится писать в стиле владельца, мониторит новости ниши и конкурентов, генерирует контент-план на неделю, показывает посты на согласование и публикует в Telegram-канал и ВКонтакте после одобрения.

---

## Цель и критерии успеха

**Боль:** фрилансер не ведёт соцсети — нет системы и времени.  
**Решение:** агент берёт на себя 90% работы, пользователю остаётся только одобрить пост кнопкой.

**Успех через 3 месяца:**
- [ ] 5 постов в неделю выходят стабильно
- [ ] Посты звучат как написал Удача, а не GPT
- [ ] 2-3 входящих от клиентов в месяц через соцсети
- [ ] Согласование одного поста ≤ 30 секунд

---

## Технический стек

| Компонент | Выбор | Причина |
|---|---|---|
| Язык | Python 3.11+ | Лучшая экосистема для AI-агентов |
| Telegram-фреймворк | aiogram 3.x | Async, современный, активная поддержка |
| AI-провайдер | OpenRouter → Claude Opus 4.8 | Ключ уже есть, лучшая модель для русского текста |
| База данных | SQLite | Один файл, ноль настройки, достаточно для 1 пользователя |
| Планировщик | APScheduler | Лёгкий, работает внутри процесса |
| Мониторинг TG | Telethon | Чтение публичных каналов конкурентов |
| Мониторинг VK | VK API | Официальный API, бесплатный |
| RSS-парсинг | feedparser | Простой, надёжный |
| Деплой | Windows Server (тот же что agent-bot) | Уже есть сервер |

---

## Архитектура системы

```
[Пользователь в Telegram]
        ↓ команды / кнопки
[aiogram Bot Handler]
        ↓
[Core Agent Logic]
    ├── StyleEngine      → строит system prompt из brand_voice
    ├── ContentPlanner   → RSS + конкуренты + topics_used → 5 тем
    ├── PostGenerator    → OpenRouter/Claude → 2 версии (TG + VK)
    ├── MemoryManager    → SQLite CRUD
    ├── ApprovalFlow     → inline-кнопки, таймауты, итерации
    └── Publisher
            ├── TelegramPublisher → Bot API sendMessage
            └── VKPublisher       → VK API wall.post
        ↓
[APScheduler]
    ├── Каждый день 08:00 → мониторинг конкурентов + RSS
    ├── Каждый понедельник 09:00 → генерация плана на неделю
    └── По расписанию → публикация одобренных постов
```

---

## База данных (SQLite)

### Таблица `brand_voice`
```sql
CREATE TABLE brand_voice (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
Хранит: `style_description`, `tone`, `forbidden_words`, `target_audience`, `business_goal`, `cta_dm`, `cta_site`, `owner_name`

### Таблица `posts`
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    post_type TEXT,          -- 'polish'/'case'/'personal'/'trend'/'selling'
    content_telegram TEXT,
    content_vk TEXT,
    status TEXT DEFAULT 'draft', -- draft/pending/approved/published/rejected/postponed
    scheduled_at DATETIME,
    published_at DATETIME,
    telegram_message_id INTEGER,
    vk_post_id INTEGER,
    reaction TEXT,           -- 'good'/'bad' — пользователь оценивает после публикации
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `topics_used`
```sql
CREATE TABLE topics_used (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    angle TEXT,
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
Скользящее окно: при генерации плана брать последние 60 записей.

### Таблица `competitor_signals`
```sql
CREATE TABLE competitor_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,             -- '@channel' или 'vk_group_id'
    source_type TEXT,        -- 'telegram'/'vk'/'rss'
    content_summary TEXT,    -- Claude извлекает тему и формат
    signal_type TEXT,        -- 'topic'/'format'/'trend'
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `settings`
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```
Ключи: `telegram_channel_id`, `vk_group_id`, `vk_token`, `telegram_competitors` (JSON-список), `vk_competitors` (JSON-список), `posting_times` (JSON), `onboarding_done`

---

## Система памяти и обучение стилю

### Онбординг (команда `/start`, если `onboarding_done = false`)

Бот проводит интервью из 7 вопросов последовательно:

```
1. "Расскажи о себе в 2-3 предложениях — кто ты и чем занимаешься?"
2. "Кто твой идеальный клиент? Опиши его — кто он, что у него болит?"
3. "Как ты общаешься с людьми — официально или как с другом?"
4. "Что тебя бесит в чужих постах про IT / веб-разработку?"
5. "Назови 3 слова, которые точно описывают твой стиль общения."
6. "Что ты никогда не напишешь в своём канале? Запрещённые слова/темы."
7. "Главная цель соцсетей — продавать услуги, строить бренд, или оба?"
```

После 7 ответов Claude Opus 4.8 генерирует `brand_voice_prompt`:

```
Ты — контент-менеджер [owner_name], веб-разработчик-фрилансер.
Стиль: [выжимка из ответов 3, 5].
Аудитория: [из ответа 2].
Запрещено: [из ответа 6].
Не нравится: [из ответа 4].
CTA для продающих постов: "Напиши мне в личку: [ссылка]"
CTA для экспертных постов: "Подробнее на сайте: [ссылка]"
Пиши просто, как говоришь. Никакого официоза.
```

Пользователь видит результат и подтверждает или редактирует → сохраняется в `brand_voice`.

**Команда `/voice`** — показывает текущий профиль стиля, можно редактировать.

### Накопление стиля

После каждой публикации бот спрашивает (через 2 часа):  
"Как зашёл этот пост? [👍 Хорошо] [👎 Не моё]"

- `reaction = 'good'` → пост добавляется как положительный пример в brand_voice (до 10 примеров)
- `reaction = 'bad'` → пост добавляется как антипример

Раз в месяц бот предлагает обновить профиль стиля на основе накопленных оценок.

---

## Генерация контент-плана

### Запуск: каждый понедельник в 09:00

### Шаги:

**Шаг 1 — Сбор сигналов:**
```python
signals = []
signals += fetch_rss(['habr.com/ru/rss/', 'vc.ru/rss', 'tproger.ru/feed/'])
signals += fetch_telegram_competitors(settings['telegram_competitors'])  # Telethon
signals += fetch_vk_competitors(settings['vk_competitors'])  # VK API
```

**Шаг 2 — Список уже использованных тем:**
```python
used = db.query("SELECT topic, angle FROM topics_used ORDER BY used_at DESC LIMIT 60")
```

**Шаг 3 — Промпт генерации плана:**
```
[brand_voice_prompt]

Составь контент-план на неделю. 5 постов по типам:
- ПН: Польза (туториал, совет, объяснение)
- ВТ: Кейс (пример из практики)
- СР: Личное (мнение, история, наблюдение)
- ЧТ: Тренд (реакция на новость из ниши)
- ПТ: Продающий (услуга, кейс с CTA на контакт)

Темы, которые уже были (не повторяй):
[список из topics_used]

Свежие сигналы из мониторинга:
[топ-10 сигналов из competitor_signals]

Новости из RSS (актуальные):
[топ-5 заголовков]

Для каждого поста:
- Тип (из списка выше)
- Заголовок темы (1 строка)
- О чём пост (1 предложение)
- Угол подачи (чем этот пост будет отличаться)
```

**Шаг 4 — Показ плана пользователю:**
```
📅 ПЛАН НА НЕДЕЛЮ [12-16 января]

ПН — 🎓 Польза
"Как я ускорил загрузку сайта в 3 раза"
Угол: не теория, а конкретные шаги которые я делал на реальном проекте

ВТ — 💼 Кейс
...

[✅ Принять план] [🔄 Перегенерировать] [✏️ Изменить тему]
```

---

## Генерация поста

### Для каждой темы из плана — генерируются ДВЕ версии:

**Промпт для Telegram:**
```
[brand_voice_prompt]

Платформа: Telegram-канал
Тип поста: [тип]
Тема: [из плана]
Угол: [из плана]
CTA: [исходя из типа]

ТРЕБОВАНИЯ:
- До 1500 знаков
- Хук в первых 1-2 строках (до "..." в превью Telegram)
- 3-5 эмодзи уместно
- Вопрос к аудитории или CTA в конце
- Пиши от первого лица

Напиши пост.
```

**Промпт для VK:**
```
[brand_voice_prompt]

Платформа: ВКонтакте
Тема и суть: [та же]

ТРЕБОВАНИЯ:
- До 3000 знаков (можно развернуть подробнее)
- Начало без хука — VK читают медленнее
- 1-3 эмодзи, не больше
- CTA в конце

Напиши пост.
```

---

## Флоу согласования

### Бот отправляет пост пользователю:

```
📝 ПОСТ [тип] | [дата публикации]
────────────────────────────
[Текст поста для Telegram]
────────────────────────────
📤 Публикация: Telegram + VK
🕐 Время: [время по расписанию]

[✅ Опубликовать]  [✏️ Переделать]
[🗑 Отклонить]     [📅 Перенести]
```

### Ветки:

**"Переделать":**
```
Бот: "Что исправить? Напиши одним сообщением."
Пользователь: "Добавь больше конкретики, убери официальный тон"
→ Claude перегенерирует пост с правкой в промпте
→ Снова на согласование

Максимум 2 итерации. После 2-й:
"Хочешь написать сам? Отправь текст и я его оформлю под платформы."
```

**"Перенести":**
```
Бот показывает: [Завтра] [Послезавтра] [Пт] [Сб] [Вс]
Пользователь выбирает дату → статус: postponed, scheduled_at обновляется
```

**"Отклонить":**
```
Статус: rejected
Тема добавляется в topics_used с меткой 'rejected' — не повторять
```

### Таймауты:
- +24 часа без ответа → напоминание: "⏰ Пост ждёт согласования"
- +48 часов → статус: postponed, пользователь уведомлён

---

## Мониторинг конкурентов

### Telethon (Telegram-каналы)

```python
# Запускается раз в день
async def monitor_telegram():
    channels = json.loads(settings['telegram_competitors'])
    for channel in channels:
        posts = await client.get_messages(channel, limit=20)
        for post in posts:
            summary = claude.extract_topic(post.text)
            db.insert_signal(source=channel, type='telegram', summary=summary)
```

Конкуренты добавляются через `/competitors add @channel_name`

### VK API

```python
# Раз в день
def monitor_vk():
    groups = json.loads(settings['vk_competitors'])
    for group_id in groups:
        posts = vk.wall.get(owner_id=-group_id, count=20)
        for post in posts['items']:
            summary = claude.extract_topic(post['text'])
            db.insert_signal(source=str(group_id), type='vk', summary=summary)
```

### RSS

```python
# Раз в день
RSS_SOURCES = [
    'https://habr.com/ru/rss/hubs/all/',
    'https://vc.ru/rss',
    'https://tproger.ru/feed/',
]

def fetch_rss():
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            db.insert_signal(source=url, type='rss', summary=entry.title)
```

---

## Публикация

### Telegram Bot API

```python
await bot.send_message(
    chat_id=settings['telegram_channel_id'],
    text=post.content_telegram,
    parse_mode='HTML'
)
```

Требование: бот добавлен в канал как администратор с правом публикации.

### VK API

```python
vk.wall.post(
    owner_id=f"-{settings['vk_group_id']}",
    message=post.content_vk,
    from_group=1
)
```

Требование: VK токен с правами `wall,offline` от имени администратора группы.  
Срок токена: 1 год (offline). Бот напоминает об обновлении за 30 дней.

### Расписание публикаций

По умолчанию: пн-пт в 10:00 по МСК (до накопления статистики).  
После 4 недель работы: APScheduler анализирует реакции пользователя (`reaction='good'`) по дням недели и часам и предлагает обновить расписание.

---

## Команды бота

| Команда | Действие |
|---|---|
| `/start` | Онбординг или главное меню |
| `/plan` | Показать или перегенерировать план на неделю |
| `/post [тема]` | Сгенерировать пост прямо сейчас |
| `/voice` | Просмотр и редактирование профиля стиля |
| `/queue` | Очередь постов на согласование |
| `/competitors` | Управление списком конкурентов |
| `/dzen [текст]` | Показать готовый текст для ручной публикации в Дзен |
| `/instagram` | Показать готовый текст для ручной публикации в Instagram |
| `/settings` | Настройки (канал, VK, время публикации) |

---

## Вне scope (v1)

| Что | Почему |
|---|---|
| Яндекс Дзен автопубликация | Нет официального API |
| Instagram автопубликация | Сложная авторизация (нужен бизнес-аккаунт + Meta App Review) |
| Генерация изображений | Отдельный модуль, не входит в v1 |
| Аналитика engagement (лайки, охваты) | Требует дополнительных токенов и API — v2 |
| Мультипользовательность | Один бот = один владелец |
| TikTok | Нет стабильного пути автопубликации |

---

## Конфигурация (.env)

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=@username_or_id
ADMIN_TELEGRAM_ID=   # Твой личный user_id для согласований

# VK
VK_TOKEN=
VK_GROUP_ID=

# OpenRouter
OPENROUTER_API_KEY=
OPENROUTER_MODEL=anthropic/claude-opus-4-8

# Telethon (для мониторинга конкурентов в TG)
TELETHON_API_ID=
TELETHON_API_HASH=
TELETHON_PHONE=      # Номер аккаунта для мониторинга

# Настройки
TIMEZONE=Europe/Moscow
DB_PATH=./data/agent.db
```

---

## Структура проекта

```
smm-agent/
├── main.py                  # Точка входа
├── .env                     # Конфигурация (не в git)
├── requirements.txt
├── data/
│   └── agent.db             # SQLite база
├── bot/
│   ├── handlers.py          # aiogram handlers
│   ├── keyboards.py         # Inline-кнопки
│   └── middlewares.py       # Проверка admin_id
├── agent/
│   ├── style_engine.py      # Онбординг + brand_voice
│   ├── content_planner.py   # Генерация плана
│   ├── post_generator.py    # Генерация постов (TG + VK версии)
│   └── memory.py            # SQLite CRUD
├── monitoring/
│   ├── rss_fetcher.py       # feedparser
│   ├── telegram_monitor.py  # Telethon
│   └── vk_monitor.py        # VK API
├── publishing/
│   ├── telegram_pub.py      # Bot API публикация
│   └── vk_pub.py            # VK API публикация
└── scheduler.py             # APScheduler задачи
```

---

## Критические риски и защита

| Риск | Защита |
|---|---|
| VK токен протухает | Напоминание за 30 дней, инструкция в боте |
| Деградация стиля | Только пользователь оценивает посты — агент не самооценивает |
| Повторяемость тем | Скользящее окно 60 записей в topics_used |
| Пользователь бросает согласование | Напоминания, кнопки прямо в Telegram, 1 тап = одобрение |
| Telethon заблокирован | Запросы раз в день, rate limiting, аккаунт с историей |
| Пост вышел с ошибкой | Команда `/delete last` — удаляет последний пост из канала |

---

## Порядок разработки (рекомендуемый)

1. **День 1-2:** SQLite схема + .env конфиг + aiogram skeleton + /start онбординг
2. **День 3-4:** StyleEngine — онбординг 7 вопросов + генерация brand_voice_prompt
3. **День 5-6:** ContentPlanner — RSS + генерация плана через Claude
4. **День 7-8:** PostGenerator — генерация TG и VK версий поста
5. **День 9-10:** ApprovalFlow — inline-кнопки, итерации, таймауты
6. **День 11-12:** TelegramPublisher + VKPublisher
7. **День 13:** APScheduler — ежедневный мониторинг + еженедельный план
8. **День 14:** Telethon мониторинг конкурентов + VK мониторинг
9. **День 15:** Финальное тестирование + деплой на сервер

**Итого MVP: ~3 недели** (Telegram + VK, без Instagram и Дзен авто)

---

*Спецификация подготовлена: 2026-06-17*  
*На основе: idea.md + research.md + critique.md*
