# KP-Agent — Production Specification v2.0

**Дата:** 2026-06-17  
**Статус:** Ready for implementation  
**Разработчик:** Claude Opus (claude-opus-4-8)  
**Версия:** 2.0 (исправленная после критики и discovery interview)

---

## Executive Summary

Персональный Telegram-бот для Александра Прохарова, который автоматизирует создание коммерческих предложений на разработку сайтов. Пользователь присылает ссылку на компанию → бот исследует бизнес, составляет ТЗ, помогает сгенерировать дизайн, создаёт мокап или живой сайт (опционально), генерирует HTML-КП в стиле kp-u-yulii.html, готовит пинг + КП + follow-up скрипты в стиле Александра, ведёт CRM-воронку и напоминает о follow-up.

**Главный принцип:** бот — инструмент продаж с памятью, а не просто документогенератор.

---

## Problem Statement

Создание одного КП занимает у Александра 2–4 часа: найти компанию, изучить бизнес, написать ТЗ, сгенерировать дизайн в ChatGPT, сверстать мокап, написать КП, придумать первое сообщение. При цели 5–10 КП в неделю — это невозможно без автоматизации.

Дополнительная боль: без follow-up системы отправленные КП уходят в пустоту. 80% продаж происходят после 2–5 касаний.

**Цель:** сократить время на одно КП до 15–20 минут активного участия при общем цикле ≤60 минут.

---

## Success Criteria

| Метрика | Цель | Реалистично |
|---|---|---|
| Время активного участия на КП | ≤20 минут | Основная цель |
| Полный цикл (ссылка → готовое КП) | ≤60 минут | Без шага «живой сайт» |
| Ответ на холодный пинг | ≥10% | Реалистично для B2B |
| КП → сделка | ≥3% | Реалистично для холодного outreach |
| Follow-up касаний на лида | 2–3 | Автоматически через бота |

---

## User Persona

**Александр Прохаров** — разработчик сайтов и AI-решений, работает один. Ищет клиентов в 2ГИС, ВКонтакте, Яндекс.Картах. Генерирует HTML-дизайны через ChatGPT — это его творческий процесс, автоматизировать не нужно. Технически грамотен: понимает API, сервисы, токены. Ценит контроль — хочет одобрять каждый ключевой шаг. Хочет диктовать правки голосом.

---

## User Journey (10 шагов)

### Шаг 0 — Квалификация (авто, мгновенно)

Александр отправляет ссылку. Бот автоматически проверяет:
- Ссылка парсится (2ГИС → определяет как 2ГИС URL, ВК → VK URL, другое → сайт компании)
- Есть ли контакты (телефон / мессенджер) для последующего outreach

Если контактов нет → бот предупреждает: *«Не нашёл контактов для связи — продолжаем?»*  
Кнопки: `✅ Да, продолжить` / `❌ Нет, пропустить`

---

### Шаг 1 — Ввод ссылки

Бот принимает:
- Карточку 2ГИС (`2gis.ru/...`)
- Страницу ВКонтакте (`vk.com/...`)
- Существующий сайт компании (любой URL)
- Яндекс.Карты (`yandex.ru/maps/...`) → парсит название → поиск через Serper

*Ответ бота:* «Принял. Начинаю исследование компании...» + прогресс в реальном времени.

---

### Шаг 2 — Исследование компании (авто, ~5 мин)

**Источники по типу ссылки:**

| Тип ссылки | Источник данных |
|---|---|
| 2ГИС | 2GIS Places API (`/3.0/items?q=&type=branch`) |
| ВКонтакте | VK API: `groups.getById` / `users.get` |
| Сайт компании | WebFetch + Cheerio (парсинг HTML) |
| Любой | Serper WebSearch по названию компании |

**Что собирает бот:**
- Название, сфера деятельности, город, адрес
- Существующий сайт (если есть): анализ качества (устаревший дизайн? нет мобильной версии? нет заявок?)
- Контакты: телефон, email, мессенджеры, соцсети
- Активность в соцсетях (есть группа ВК? последний пост когда?)
- Конкуренты в нише: топ-3 по запросу `{сфера} {город}` через Serper
- **Конкретная боль:** что именно мешает продажам (нет сайта / устаревший / нет формы заявки / нет адаптива / нет SEO)

**По завершении:** бот отправляет структурированную сводку + выявленную главную боль.

```
🏢 Название: Шиномонтаж «Колесо»
📍 Город: Новосибирск, ул. Ленина, 15
📞 Контакты: +7-913-XXX-XX-XX (найдено в 2ГИС)
🌐 Сайт: нет
📱 ВКонтакте: есть, последний пост 8 месяцев назад
⚠️ Боль: нет сайта + клиенты звонят, нет онлайн-записи
🏆 Конкуренты с сайтом: ШинМастер.рф, КолесоПрофи.ру
```

Кнопки: `✅ Продолжить` / `✏️ Уточнить`

---

### Шаг 3 — Утверждение брифа

Александр читает сводку и:
- Нажимает «Продолжить» — бот идёт дальше
- Диктует или пишет правки — бот обновляет сводку и снова показывает

---

### Шаг 4 — Автогенерация ТЗ (авто, ~3 мин)

Бот самостоятельно составляет техническое задание на сайт:
- **Тип сайта** (определяет по сфере и контексту: лендинг / корпоративный / каталог)
- **Структура и блоки** (какие секции нужны: hero, услуги, цены, отзывы, форма, карта, контакты)
- **УТП и ключевые смыслы** (из исследования: что отличает этот бизнес)
- **Целевая аудитория** (вывод из сферы и гео)
- **Цветовой тон** (определяет по сфере: еда→тёплые, медицина→чистые, авто→тёмные/промышленные)
- **Функциональность** (онлайн-запись? форма заявки? калькулятор? карта?)
- **Форма заявки** → уведомление в Telegram Александра (Netlify Forms)

Бот генерирует ТЗ-документ и ChatGPT-промпт для дизайна.

*Сообщение бота:* «Вот ТЗ и промпт для дизайна. Проверь.»  
Кнопки: `✅ Подтвердить` / `✏️ Скорректировать`

---

### Шаг 5 — Получение HTML-дизайна (ручной шаг, ~20 мин)

Бот отправляет:
1. ТЗ-документ (текст)
2. Готовый промпт для ChatGPT (скопировать и вставить)

*Бот:* «Скопируй промпт в ChatGPT, сгенерируй дизайн и пришли мне HTML-файл. Жду.»

Александр генерирует дизайн в ChatGPT, скачивает HTML, присылает боту.

**Валидация файла:**
- Проверить MIME-type: только `text/html`
- Если прислал изображение → *«Мне нужен HTML-файл, а не картинка. Сохрани из ChatGPT как .html»*
- Если прислал PDF → *«Нужен HTML-файл. В ChatGPT нажми "Export" → HTML»*
- Проверить базовую структуру: `<html>`, `<body>` должны быть в файле
- Предупредить если внешние CSS-файлы: *«Файл ссылается на внешние стили. Лучше попросить ChatGPT сделать всё inline — хочешь переделать?»*

---

### Шаг 6 — Мокап или живой сайт (опциональный, авто)

**Бот спрашивает каждый раз:**

```
🤔 Что делаем с дизайном?

[🎨 Мокап] — быстро (~5 мин, сайт не деплоится)
Показываю блоки структуры с реальным контентом клиента.
В КП будет схема страницы, без живой ссылки.

[🌐 Живой сайт] — медленнее (~15 мин, деплоится на Netlify)
Генерирую полноценный сайт с реальным контентом и деплою.
В КП будет живая ссылка на превью.
```

**Если мокап:**
- Бот генерирует HTML-структуру с заполненным контентом (заголовок, текст, блоки) — это НЕ деплоится
- Добавляет в КП как «структура будущего сайта»

**Если живой сайт:**
1. Бот берёт HTML-дизайн от Александра
2. Claude Opus анализирует структуру, цвета, блоки
3. Генерирует новый HTML заполненный реальным контентом из исследования
4. **Требования к генерируемому HTML:**
   - Все стили — inline или в теге `<style>` (никаких `href` на внешние CSS)
   - Google Fonts можно через `<link>` в `<head>` (только шрифты)
   - Все картинки — через URL (Unsplash / stock-фото) или placeholder
   - Форма с `data-netlify="true"` и `name="contact"` → уведомления через Netlify Forms
   - Адаптив: мобильная версия обязательна
5. Деплой на Netlify:
   - `POST https://api.netlify.com/api/v1/sites` → получить `site_id`
   - Упаковать HTML в ZIP
   - `POST https://api.netlify.com/api/v1/sites/{site_id}/deploys` → получить `deploy_id`
   - **Polling:** `GET /deploys/{deploy_id}` каждые 5 сек, timeout 3 минуты
   - Когда `state === 'ready'` → отправить ссылку
6. Показывает: `✅ Сайт готов: https://kp-{uuid}.netlify.app`

*Кнопки:* `✅ Отлично, делаем КП` / `✏️ Правки`

**Правки к сайту (максимум 3 итерации):**
- Александр диктует или пишет что изменить
- Бот применяет правки к HTML (читает текущий файл, вносит изменения, деплоит заново)
- После 3 итераций: *«Исчерпал лимит правок. Продолжаем с текущей версией или хочешь начать сначала?»*

---

### Шаг 7 — Генерация HTML-КП (авто, ~3 мин)

Бот создаёт HTML-презентацию в стиле `kp-u-yulii.html`.

**Стиль (few-shot из шаблона):**
- Тёмный фон `#0F0B08`, золотые акценты `#C8A96E`
- Шрифты: Playfair Display (заголовки) + Inter (текст)
- Слайдовая структура (scroll-snap, full-viewport секции)
- Навигационные точки справа
- Карточки с золотыми бордерами
- Чеклисты с золотой галочкой ✓
- Нумерация слайдов (01 / 07)

**Структура КП (7 слайдов):**

1. **Обложка** — имя компании, дата, «Подготовил: Александр», действует 14 дней
2. **Что уже сделано** — мокап/прототип компании (схема или ссылка)
3. **Анализ текущего положения** — что сейчас болит (нет сайта / устаревший / нет заявок)
4. **Что получите** — состав работ из ТЗ (чеклист по блокам)
5. **Этапы и сроки** — из прайс-листа (шаги, дни, результат каждого)
6. **Цена** — из прайс-листа по категории, с включёнными позициями
7. **Об Александре** — краткое портфолио + CTA (кнопка «Обсудить проект» → Telegram)

**Стиль текстов в КП (на основе kp-u-yulii.html + накопленных правок Александра):**
- Живо, без канцелярщины
- Конкретные цифры и факты о компании
- Не «мы сделаем сайт», а «вот что конкретно получит ваш бизнес»
- Разговорный русский, без официоза

После генерации: бот отправляет HTML-файл + краткое превью.  
Кнопки: `✅ Подтвердить` / `✏️ Правки`

**Правки к КП (максимум 3 итерации):**
- Голосом или текстом: «поменяй цену на 30 000», «добавь пункт про SEO»
- Бот вносит правки и показывает снова

---

### Шаг 8 — Деплой КП (авто)

После подтверждения КП:
1. Бот деплоит финальный HTML на отдельный Netlify site
2. Polling до `state=ready`
3. Отправляет: `✅ КП готово: https://kp-{компания}-{uuid}.netlify.app`

Сохраняет: `kp_url`, `kp_html`, дата деплоя.

---

### Шаг 9 — Генерация скриптов (авто, ~2 мин)

Бот генерирует 4 текста **в стиле Александра** (на основе kp-u-yulii.html + накопленных примеров):

**1. Пинг — первое холодное сообщение (2–3 строки):**
```
Привет! Заметил, у вас нет сайта — а у конкурентов Колесо-Сервис и ШинМастер уже есть.
Сделал небольшой набросок как мог бы выглядеть ваш. Показать?
```
Правило: конкретная боль этого бизнеса + интрига (набросок готов), без слова «коммерческое предложение».

**2. Сообщение с КП (3–4 строки):**
```
Отправляю как и обещал — вот КП по сайту для вашего шиномонтажа:
{ссылка на КП}
Там прототип, состав работ и цена. Посмотрите, если что — пишите.
```

**3. Follow-up через 3 дня (если нет ответа):**
```
Добрый день! Хотел уточнить — успели посмотреть КП?
```

**4. Follow-up через 7 дней:**
```
Ещё раз привет. КП актуально ещё 7 дней — если интересно, давайте обсудим.
```

**5. Ответы на возражения (3 карточки):**
- «Дорого» → конкретный ответ о ценности
- «Уже есть сайт» → про устаревший дизайн
- «Не сейчас» → про конкурентов которые не ждут

Каждый текст — в отдельном блоке, готово к копипасту.

---

### Шаг 10 — CRM-запись

Бот автоматически создаёт запись в воронке:

```
📊 КП #42 создано
🏢 Шиномонтаж «Колесо», Новосибирск
💰 Лендинг, 25 000 ₽
📅 17 июня 2026
📌 Статус: пинг не отправлен
```

Напоминает:
- **+3 дня:** «Ты отправлял пинг в Шиномонтаж Колесо? Отметь статус.»
- **+7 дней:** «Follow-up #2 по Шиномонтаж Колесо — вот текст, скопируй и отправь.»

---

## Bot Commands

| Команда | Что делает |
|---|---|
| `/start` | Приветствие + инструкция (отправить ссылку) |
| `/history` | Список всех КП: название, дата, статус, цена |
| `/status` | Текущее активное КП: какой шаг, что ждёт |
| `/outcome {id}` | Отметить результат: replied / call / deal / rejected |
| `/price` | Посмотреть прайс-лист (можно редактировать) |
| `/cancel` | Отменить текущее КП |

**Управление прайсом через `/price`:**
```
/price set landing 30000 5    → изменить цену лендинга
/price list                   → показать текущий прайс
```

---

## Style Learning System

**Цель:** все тексты, генерируемые ботом, должны звучать как Александр, а не как ChatGPT.

### Базовые материалы (Few-Shot)

Системный промпт каждого текстового запроса содержит:

```
## СТИЛЬ АВТОРА

Ты пишешь от имени Александра. Используй его стиль — изучи примеры ниже.

### Пример КП (структура и тон):
{содержимое kp-u-yulii.html — только текстовые блоки без CSS}

### Накопленные примеры правок:
{style_corrections из SQLite — последние 20 записей}
```

### Механизм накопления правок

Каждый раз когда Александр правит текст бота:
1. Бот сохраняет пару: `{оригинал}` → `{правка}`
2. Запись в таблице `style_corrections` (SQLite)
3. Тип правки: `kp_text` / `ping` / `followup` / `objection`

Пример:
```json
{
  "type": "ping",
  "original": "Добрый день! Я разработчик сайтов и хотел бы предложить вам...",
  "corrected": "Привет! У вас нет сайта, а конкурент уже получает заявки с интернета.",
  "created_at": "2026-06-17T10:00:00Z"
}
```

В системный промпт включаются последние 20 правок по типу + шаблон kp-u-yulii.html.

### Команда `/style`

```
/style add ping "Привет! [конкретная проблема]. Сделал кое-что — покажу?"
→ добавляет как эталонный пример пинга
```

---

## Technical Architecture

### Стек

| Компонент | Технология | Версия |
|---|---|---|
| Язык | Node.js | 22.x |
| Telegram | grammy | ^1.x |
| AI | Anthropic Claude | claude-opus-4-8 |
| Голос | Deepgram API (или Whisper local) | |
| Поиск | Serper API | |
| Парсинг сайтов | undici + cheerio | |
| 2ГИС | 2GIS Places API (dev.2gis.ru) | v3 |
| ВКонтакте | VK API | v5.199 |
| Деплой превью | Netlify API | v1 |
| База данных | better-sqlite3 | |
| Хранилище БД | Railway Volume | /data/kp-agent.db |
| Хостинг | Railway | |
| ZIP | archiver | |

**Почему better-sqlite3 вместо sql.js:** синхронный API, в 10× быстрее для запросов, нативные бинарники на Railway Linux работают без проблем.

---

### Модель данных

```sql
-- Проекты (КП)
CREATE TABLE projects (
  id TEXT PRIMARY KEY,        -- uuid
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  status TEXT NOT NULL,       -- enum: см. State Machine
  
  -- Источник
  org_link TEXT NOT NULL,     -- исходная ссылка
  link_type TEXT,             -- '2gis' | 'vk' | 'site' | 'other'
  
  -- Исследование
  org_name TEXT,
  org_city TEXT,
  org_industry TEXT,
  org_pain TEXT,              -- главная боль (текст)
  org_contacts JSON,          -- {phone, email, vk, telegram}
  org_data JSON,              -- полный JSON исследования
  
  -- ТЗ
  tz_type TEXT,               -- 'landing' | 'corporate' | 'catalog' | 'ecommerce'
  tz_doc TEXT,                -- ТЗ-документ (markdown)
  chatgpt_prompt TEXT,        -- промпт для ChatGPT
  
  -- Дизайн и сайт
  design_html TEXT,           -- HTML от пользователя (дизайн)
  preview_type TEXT,          -- 'mockup' | 'site'
  preview_html TEXT,          -- сгенерированный HTML
  preview_url TEXT,           -- Netlify URL (если site)
  netlify_site_id TEXT,       -- для последующих обновлений
  
  -- КП
  kp_html TEXT,               -- HTML КП
  kp_url TEXT,                -- Netlify URL КП
  netlify_kp_site_id TEXT,
  
  -- Скрипты
  scripts JSON,               -- {ping, kp_message, followup_3d, followup_7d, objections}
  
  -- Прайс
  price INTEGER,              -- итоговая цена (руб)
  days INTEGER,               -- срок (дни)
  
  -- CRM воронка
  outcome TEXT DEFAULT 'pending',  -- 'pending'|'pinged'|'replied'|'call'|'deal'|'rejected'
  pinged_at TEXT,             -- дата отправки пинга
  kp_sent_at TEXT,            -- дата отправки КП
  followup_3d_sent INTEGER DEFAULT 0,
  followup_7d_sent INTEGER DEFAULT 0,
  outcome_notes TEXT          -- заметки о результате
);

-- Правки стиля (few-shot learning)
CREATE TABLE style_corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  type TEXT NOT NULL,         -- 'ping' | 'kp_text' | 'followup' | 'objection'
  original TEXT NOT NULL,
  corrected TEXT NOT NULL
);

-- Примеры стиля (вручную добавленные через /style)
CREATE TABLE style_examples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  type TEXT NOT NULL,
  example TEXT NOT NULL,
  label TEXT                  -- необязательное описание
);

-- Прайс-лист
CREATE TABLE price_list (
  type TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  price INTEGER NOT NULL,
  days INTEGER NOT NULL
);
```

---

### State Machine

```
CREATED
  → RESEARCHING          (шаг 2: идёт исследование)
  → AWAITING_BRIEF       (шаг 3: ждём одобрение брифа)
  → GENERATING_TZ        (шаг 4: генерация ТЗ)
  → AWAITING_TZ          (шаг 4: ждём одобрение ТЗ)
  → AWAITING_DESIGN      (шаг 5: ждём HTML-файл от пользователя)
  → CHOOSING_PREVIEW     (шаг 6: ждём выбор мокап/сайт)
  → BUILDING_PREVIEW     (шаг 6: генерация и деплой)
  → AWAITING_PREVIEW     (шаг 6: ждём одобрение превью)
  → GENERATING_KP        (шаг 7: генерация КП)
  → AWAITING_KP          (шаг 7: ждём одобрение КП)
  → DEPLOYING_KP         (шаг 8: деплой КП)
  → GENERATING_SCRIPTS   (шаг 9: генерация скриптов)
  → DONE                 (все скрипты готовы, ждём outreach)
  → CANCELLED            (отменён командой /cancel)
```

---

### Netlify Deploy — правильная последовательность

```javascript
// Шаг 1: создать сайт
const site = await netlify.post('/sites', {
  name: `kp-${project.id.slice(0,8)}`
});
const siteId = site.id;

// Шаг 2: упаковать HTML в ZIP
const zip = archiver('zip');
zip.append(htmlContent, { name: 'index.html' });
const zipBuffer = await finalizeZip(zip);

// Шаг 3: деплой
const deploy = await netlify.post(`/sites/${siteId}/deploys`, zipBuffer, {
  headers: { 'Content-Type': 'application/zip' }
});

// Шаг 4: polling до ready (timeout 3 min)
let ready = false;
const start = Date.now();
while (!ready) {
  if (Date.now() - start > 180_000) throw new Error('Deploy timeout');
  await sleep(5000);
  const status = await netlify.get(`/deploys/${deploy.id}`);
  ready = status.state === 'ready';
}

return `https://${site.subdomain}.netlify.app`;
```

---

### 2GIS Places API

```javascript
// Поиск по URL компании в 2ГИС
// URL формат: https://2gis.ru/novosibirsk/firm/70000001043420091

// Извлечь firm_id из URL:
const firmId = url.match(/\/firm\/(\d+)/)?.[1];

// Запрос к API
const response = await fetch(
  `https://catalog.api.2gis.ru/3.0/items/byid` +
  `?id=${firmId}&key=${process.env.TWOGIS_API_KEY}` +
  `&fields=items.point,items.contact_groups,items.schedule,items.rubrics`
);

// Если 2ГИС не дал firm_id — fallback: Serper поиск по названию
```

---

### VK API

```javascript
// Для группы (vk.com/public123456 или vk.com/cafe_name)
const response = await fetch(
  `https://api.vk.com/method/groups.getById` +
  `?group_id=${groupId}&access_token=${process.env.VK_TOKEN}` +
  `&fields=description,contacts,site,activity,city&v=5.199`
);

// Для пользователя (vk.com/id123 или vk.com/username)
// groups.getById не подходит — использовать users.get
```

---

### Голосовые сообщения

```javascript
// Получаем voice из Telegram
const fileUrl = await bot.api.getFile(ctx.message.voice.file_id);
const oggBuffer = await downloadFile(fileUrl);

// Deepgram (приоритет)
if (process.env.DEEPGRAM_API_KEY) {
  const transcript = await deepgram.listen.prerecorded.transcribeFile(
    oggBuffer,
    { model: 'nova-2', language: 'ru' }
  );
  return transcript.results.channels[0].alternatives[0].transcript;
}

// Fallback: Whisper (если нет Deepgram)
// Через OpenAI API или локальный whisper.cpp
```

---

### Follow-up Scheduler

```javascript
// При запуске бота — проверяем просроченные follow-up
async function checkFollowUps() {
  const now = new Date();
  
  const projects = db.prepare(`
    SELECT * FROM projects 
    WHERE outcome IN ('pending', 'pinged')
    AND pinged_at IS NOT NULL
  `).all();
  
  for (const p of projects) {
    const daysSince = (now - new Date(p.pinged_at)) / 86_400_000;
    
    if (daysSince >= 3 && !p.followup_3d_sent) {
      await sendFollowUpReminder(p, 3);
    }
    if (daysSince >= 7 && !p.followup_7d_sent) {
      await sendFollowUpReminder(p, 7);
    }
  }
}

// Запускать каждые 2 часа
setInterval(checkFollowUps, 2 * 60 * 60 * 1000);
```

---

## Functional Requirements

### P0 — Must Have

- [ ] Принять и определить тип ссылки (2ГИС / ВК / сайт)
- [ ] Исследование через 2GIS API, VK API, WebFetch, Serper
- [ ] Автогенерация ТЗ + ChatGPT-промпт
- [ ] Приём и валидация HTML-файла от пользователя
- [ ] Выбор мокап/живой сайт (вопрос на каждом КП)
- [ ] Деплой на Netlify через API (2 шага + polling)
- [ ] Генерация КП в стиле kp-u-yulii.html (few-shot)
- [ ] Деплой КП на отдельный Netlify site
- [ ] Генерация пинга + КП-сообщения + 2 follow-up + 3 ответа на возражения
- [ ] Кнопки одобрения (InlineKeyboard) на каждом шаге
- [ ] Правки голосом (Deepgram / Whisper)
- [ ] Правки текстом на любом шаге (≤3 итерации)
- [ ] State machine — прогресс сохраняется в SQLite при рестарте
- [ ] OWNER_ID lock — только Александр
- [ ] /history, /status, /outcome, /price, /cancel, /style

### P1 — Should Have

- [ ] Follow-up напоминания через 3 и 7 дней
- [ ] CRM-воронка с /outcome
- [ ] Накопление и применение правок стиля (style_corrections)
- [ ] Квалификация на шаге 0 (есть ли контакты)
- [ ] Прогресс-апдейты в чате во время фоновой работы (что делает бот)
- [ ] Idempotency: защита от дублирования при переотправке сообщения
- [ ] Error handling для всех внешних API (см. раздел ниже)

### P2 — Nice to Have

- [ ] Скриншот превью через Playwright (отправить в чат как картинку)
- [ ] Статистика воронки: `/stats` — по неделям/месяцам
- [ ] Обучение на выигранных сделках: анализ успешных КП
- [ ] Трекинг просмотра КП (1×1 pixel через CF Worker)

---

## Error Handling

| Ситуация | Поведение бота |
|---|---|
| 2ГИС URL, фирма не найдена | «Не нашёл компанию в 2ГИС — попробую поискать по названию» → Serper fallback |
| VK API недоступен | «Не получилось достать данные из ВК — продолжу с тем что есть» |
| Netlify deploy timeout (>3 мин) | «Деплой завис. Попробовать ещё раз?» + кнопки Retry / Skip |
| Claude API error / timeout | Retry 3 раза с exponential backoff, потом: «Возникла ошибка, попробуй ещё раз» |
| Пользователь прислал не HTML | «Жду .html файл. Открой ChatGPT → Download → HTML» |
| Пользователь прислал HTML с внешними CSS | Предупреждение + вопрос переделать |
| Бот перезапустился в середине процесса | При `/start` или первом сообщении: «Есть незавершённое КП для {компания}, продолжим?» |
| Превышен лимит итераций правок (3) | «Исчерпал лимит правок. Продолжаем с текущей версией?» |

---

## Non-Functional Requirements

| Требование | Значение |
|---|---|
| Производительность | Автоматические шаги (2, 4, 6, 7) — ≤30 мин суммарно |
| Доступность | Railway обеспечивает 99.5%+ uptime |
| Надёжность данных | SQLite на Railway Volume — переживает редеплой |
| Масштаб | 5–10 КП/неделю (текущая нагрузка) |
| Безопасность | OWNER_ID проверяется на каждом апдейте |
| Логирование | Каждый шаг логируется с timestamp и project_id |
| Идемпотентность | grammy session + проверка дублей по message_id |

---

## Deployment

### Railway конфигурация

```
Service: kp-agent
Region: eu-west (ближе к Новосибирску чем US)
Volume: /data (1GB минимум)
```

### `railway.toml`

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "node src/index.js"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[volumes]]
mountPath = "/data"
```

### `.env` (переменные в Railway)

```env
BOT_TOKEN=                    # Telegram Bot Token
OWNER_ID=                     # Telegram user ID Александра
ANTHROPIC_API_KEY=            # Claude Opus
NETLIFY_TOKEN=                # Netlify Personal Access Token
SERPER_API_KEY=               # Serper.dev
TWOGIS_API_KEY=               # dev.2gis.ru
VK_TOKEN=                     # VK Service Token
DEEPGRAM_API_KEY=             # Опционально (Deepgram для голоса)
DB_PATH=/data/kp-agent.db    # SQLite на Volume
```

---

## Project Structure

```
kp-agent/
├── src/
│   ├── index.js              # точка входа, инициализация grammy
│   ├── bot.js                # регистрация хендлеров
│   ├── db.js                 # инициализация SQLite, миграции
│   ├── config.js             # прайс-лист, константы
│   │
│   ├── flows/
│   │   ├── research.js       # шаги 0-3: квалификация, исследование, бриф
│   │   ├── tz.js             # шаг 4: ТЗ + ChatGPT промпт
│   │   ├── design.js         # шаг 5: приём дизайна
│   │   ├── preview.js        # шаг 6: мокап/сайт + Netlify
│   │   ├── kp.js             # шаг 7-8: КП + деплой
│   │   └── scripts.js        # шаг 9: пинг + follow-up + возражения
│   │
│   ├── commands/
│   │   ├── history.js
│   │   ├── status.js
│   │   ├── outcome.js
│   │   ├── price.js
│   │   ├── style.js
│   │   └── cancel.js
│   │
│   ├── services/
│   │   ├── claude.js         # обёртка над Anthropic API
│   │   ├── netlify.js        # deploy + polling
│   │   ├── twogis.js         # 2GIS Places API
│   │   ├── vk.js             # VK API
│   │   ├── serper.js         # WebSearch
│   │   ├── parser.js         # WebFetch + Cheerio
│   │   ├── voice.js          # Deepgram / Whisper
│   │   └── followup.js       # scheduler для напоминаний
│   │
│   └── prompts/
│       ├── research.js       # системный промпт для исследования
│       ├── tz.js             # промпт для ТЗ
│       ├── site.js           # промпт для генерации HTML сайта
│       ├── kp.js             # промпт для КП (с few-shot kp-u-yulii.html)
│       └── scripts.js        # промпт для скриптов (с few-shot стиля)
│
├── assets/
│   └── kp-u-yulii.html       # шаблон КП для few-shot (копия из репо)
│
├── package.json
├── railway.toml
└── .env.example
```

---

## Прайс-лист (начальное значение)

```javascript
// src/config.js
export const PRICE_LIST = {
  landing:   { label: 'Лендинг',          price: 25000, days: 5  },
  corporate: { label: 'Корпоративный',    price: 45000, days: 10 },
  catalog:   { label: 'Каталог товаров',  price: 65000, days: 14 },
  ecommerce: { label: 'Интернет-магазин', price: 90000, days: 21 },
};
```

Изменяется через `/price set {type} {price} {days}` и сохраняется в SQLite.

---

## Out of Scope (V1)

- Instagram (заблокирован в России с 2019, нарушение ToS)
- Авто-отправка сообщений клиентам (только скрипты для копипаста)
- Мультипользовательский режим
- CMS/панель управления для клиента
- Яндекс.Карты (использовать Serper-поиск по названию вместо парсинга)
- Playwright/скриншоты (V2)

---

## Pre-Development Checklist

Перед началом разработки необходимо:

- [ ] Создать аккаунт на netlify.com → получить Personal Access Token
- [ ] Зарегистрироваться на dev.2gis.ru → получить API Key
- [ ] Создать VK App на dev.vk.com → получить Service Token
- [ ] Зарегистрироваться на serper.dev → получить API Key
- [ ] Создать Telegram Bot через @BotFather → получить BOT_TOKEN
- [ ] Создать Railway проект + Volume → получить Railway token для CI (опционально)
- [ ] Опционально: создать аккаунт Deepgram → получить API Key для голоса
- [ ] Скопировать `kp-u-yulii.html` в `assets/` репозитория бота

---

## Open Questions

1. **Deepgram vs Whisper:** у Александра уже есть Deepgram ключ (в Jarvis-боте)? Если да — переиспользовать. Если нет — использовать OpenAI Whisper API (есть ли ключ OpenAI?).
2. **Netlify Forms уведомления:** куда должны приходить заявки с сайтов-превью? В Telegram Александра (через Netlify webhook → Telegram) или только email?
3. **Serper API:** есть ли уже ключ в smeta-bot или нужен новый?

---

## Appendix: Key Technical Decisions

| Решение | Причина |
|---|---|
| claude-opus-4-8 для всего | Максимальное качество текстов и HTML-генерации |
| better-sqlite3 вместо sql.js | Синхронный API, быстрее, проще в use |
| Railway Volume для SQLite | Данные переживают редеплой (ephemeral filesystem на Railway) |
| Netlify (не Vercel) | Прямой API для деплоя ZIP без git, бесплатный тир 500 сайтов |
| Few-shot через kp-u-yulii.html | Единственный реальный пример стиля Александра |
| Ping → KP (не сразу КП) | Реальная конверсия: пинг 10%, КП у тёплых 20-30% vs 1-2% холодного КП |
| 2GIS API вместо WebFetch | 2ГИС = SPA, WebFetch возвращает пустой HTML |
| Instagram — Out of scope | Заблокирован в RU с 2019, любой scraping нарушает ToS |
| Мокап по умолчанию (бот спрашивает) | Живой сайт до продажи = риск бесплатной работы |
