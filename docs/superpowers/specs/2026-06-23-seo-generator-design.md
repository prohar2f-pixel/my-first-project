# SEO Generator — Design

**Дата:** 2026-06-23
**Проект:** `C:\Users\Udacha\Documents\projects\aeo-generator\` (домен aeo.aiprohar.ru)

## Цель

Добавить к существующему AEO-генератору вторую страницу — **SEO-генератор**. Пользователь вставляет ссылку на сайт → AI анализирует → форма заполняется автоматически → на выходе полный пакет файлов для технической SEO-оптимизации (бесплатный органический трафик, рост в выдаче Google/Яндекс).

## Контекст

AEO-генератор уже работает: одна страница `index.html` с формой данных бизнеса, AI-анализатором (Cloudflare Worker `aeo-analyzer`), генерацией файлов (`generator.js`), UI-логикой (`app.js`), счётчиком использований и сбором email-лидов.

Форма ввода для SEO **идентична** AEO (те же данные бизнеса). Отличается только пакет файлов на выходе. Поэтому код формы и анализатора общий.

## Архитектура (подход A — общий код, две тонкие страницы)

Общие функции выносятся в `js/shared.js`, который подключают обе страницы. Каждая страница имеет свой файл генераторов и свой UI-файл с `generate()` / `downloadZip()`.

### Файлы

**Новые:**
- `seo.html` — структура как у `index.html` (header, how-it-works, форма, output-card), но:
  - заголовок про SEO («Сделай сайт первым в Google и Яндекс»)
  - 4 SEO-вкладки в output вместо 5 AEO-вкладок
  - подключает `shared.js` + `seo-generator.js` + `seo-app.js`
- `js/shared.js` — общие функции, вынесенные из `app.js`:
  - константы `WORKER_URL`, `CONTACT_URL`, `COUNTER_URL`, `COUNTER_BASE`
  - `loadCounter()`, `incrementCounter()`
  - `submitLead()`
  - `analyzeUrl()`
  - `collectFormData()`
  - `switchTab(name)`, `copyTab()`
  - вызов `loadCounter()` при загрузке
- `js/seo-generator.js` — чистые функции генерации SEO-файлов (без DOM):
  - `generateTitleDesc(data)`
  - `generateOgTwitter(data)`
  - `generateLocalBusiness(data)`
  - `generateSeoChecklist(data)`
- `js/seo-app.js` — `generate()` и `downloadZip()` для SEO-страницы

**Меняются:**
- `js/app.js` — удалить функции, переехавшие в `shared.js`. Остаётся только AEO-`generate()` и AEO-`downloadZip()`.
- `index.html` — добавить переключатель вверху, подключить `shared.js` перед `app.js`.

### Подключение скриптов

- `index.html`: JSZip → `generator.js` → `shared.js` → `app.js`
- `seo.html`: JSZip → `seo-generator.js` → `shared.js` → `seo-app.js`

`generate()` и `downloadZip()` определены в `app.js` (AEO) и в `seo-app.js` (SEO) с одинаковыми именами — конфликта нет, т.к. каждая страница подключает только свой UI-файл.

### Переключатель AEO / SEO

Две вкладки-ссылки в шапке обеих страниц, без JS:

```html
<nav class="mode-switch">
  <a href="index.html" class="mode-tab active">AEO</a>
  <a href="seo.html" class="mode-tab">SEO</a>
</nav>
```

На `index.html` класс `active` у AEO, на `seo.html` — у SEO. Стили `.mode-switch` / `.mode-tab` добавляются в `css/style.css` (общий для обеих страниц).

## SEO-пакет (output)

Объект `data` — тот же, что в `collectFormData()`: `{ url, name, jobTitle, phone, email, telegram, city, lang, services[], faq[] }`.

### 1. `generateTitleDesc(data)`
Возвращает оптимизированные теги:
```html
<title>{name} — {jobTitle} в {city} | Цены и запись</title>
<meta name="description" content="{jobTitle} {name} в городе {city}. {услуги через запятую}. Запись по телефону {phone}.">
```
- title до ~60 символов, description до ~160 символов (обрезка по длине).
- Если поля пустые — собираем из того, что есть (минимум name + url).

### 2. `generateOgTwitter(data)`
```html
<meta property="og:type" content="website">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="{url}/">
<meta property="og:image" content="{url}/og-image.jpg">
<meta property="og:locale" content="ru_RU">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="...">
<meta name="twitter:description" content="...">
<meta name="twitter:image" content="{url}/og-image.jpg">
```
title/description берутся из той же логики, что в `generateTitleDesc`. `og:image` — путь-заглушка, в чеклисте напоминаем загрузить картинку 1200×630.

### 3. `generateLocalBusiness(data)`
JSON-LD `LocalBusiness` из имеющихся полей:
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{name}",
  "url": "{url}/",
  "telephone": "{phone}",
  "email": "{email}",
  "address": { "@type": "PostalAddress", "addressLocality": "{city}", "addressCountry": "RU" },
  "areaServed": "{city}",
  "priceRange": "{из услуг: min–max ₽}",
  "sameAs": ["{telegram url}"]
}
```
- Поля добавляются только если заполнены (как в существующем `generateJsonLd`).
- Оборачивается в `<script type="application/ld+json">`.
- Адрес (улица), часы работы, гео-координаты, рейтинг форма не собирает → их нет в разметке, вместо этого они в чеклисте как «добавь вручную».

### 4. `generateSeoChecklist(data)`
Текстовый чеклист (`.txt`) с галочками `[ ]` / `[x]`. Пункты, которые мы УЖЕ закрыли пакетом, отмечены `[x]`; остальное — `[ ]` с инструкцией:
- `[x]` Title и meta description
- `[x]` Open Graph / Twitter Card
- `[x]` LocalBusiness разметка
- `[ ]` Один `<h1>` на странице с главным ключом
- `[ ]` `alt` у всех картинок
- `[ ]` Картинка og-image.jpg 1200×630
- `[ ]` Адрес и часы работы в LocalBusiness
- `[ ]` Скорость загрузки (сжать картинки, проверить в PageSpeed Insights)
- `[ ]` Внутренние ссылки между страницами
- `[ ]` Зарегистрировать сайт в Яндекс.Вебмастер
- `[ ]` Зарегистрировать сайт в Google Search Console

## ZIP-пакет (`downloadZip` в seo-app.js)

| Файл | Источник |
|------|----------|
| `title-description.html` | `generateTitleDesc` |
| `og-twitter.html` | `generateOgTwitter` |
| `localbusiness.html` | `generateLocalBusiness` |
| `seo-checklist.txt` | `generateSeoChecklist` |

Имя архива: `seo-package.zip`.

## Поток данных

1. Пользователь на `seo.html` вводит URL → `analyzeUrl()` (shared) → Worker возвращает данные → форма заполняется.
2. Кнопка «Сгенерировать SEO-пакет» → `generate()` (seo-app) → `collectFormData()` (shared) → 4 функции из `seo-generator.js` → текст в `<pre>` вкладок → `incrementCounter()`.
3. `switchTab` / `copyTab` (shared) работают по тем же `.tab-btn` / `.tab-panel`.
4. ZIP — `downloadZip()` (seo-app).

## Обработка ошибок

Без изменений к существующему поведению: `analyzeUrl` показывает ошибку в `#analyze-status`; `generate` требует минимум `url` + `name` (alert). Пустые поля в генераторах пропускаются.

## Что НЕ делаем (YAGNI)

- Не трогаем существующий AEO-функционал, кроме выноса общих функций.
- Не добавляем сбор адреса/часов/гео в форму (вместо этого — пункты чеклиста).
- Не чиним счётчик `countapi.xyz` в рамках этой задачи (отдельный вопрос).
- Не делаем единый «AEO+SEO» ZIP — у каждой страницы свой пакет.

## Тестирование

Ручная проверка в браузере (двойной клик по `seo.html`):
- Переключатель AEO ⇄ SEO работает (ссылки ведут на нужные страницы, активная подсвечена).
- AEO-страница (`index.html`) по-прежнему генерит и качает ZIP (не сломалась после рефакторинга).
- На SEO: анализ URL заполняет форму; «Сгенерировать» показывает 4 вкладки; копирование работает; ZIP качается с 4 файлами.
- JSON-LD из LocalBusiness валиден (проверка в validator.schema.org).

## Деплой

Коммит + push в `main` репозитория `aeo-generator`. GitHub Pages подхватит `seo.html` автоматически (доступна по `aeo.aiprohar.ru/seo.html`).
