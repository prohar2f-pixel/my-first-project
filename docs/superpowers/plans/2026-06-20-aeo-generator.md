# AEO Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить отдельный сайт-генератор AEO-пакета: пользователь вводит данные бизнеса → получает готовые файлы (robots.txt, sitemap.xml, мета-теги, JSON-LD, FAQ HTML) в ZIP-архиве.

**Architecture:** Статический сайт (pure HTML/CSS/JS), без сборщиков и npm. Логика генерации вынесена в `js/generator.js` (чистые функции, нет DOM-зависимостей). UI-логика в `js/app.js`. JSZip подключается через CDN для упаковки файлов в ZIP.

**Tech Stack:** HTML5, CSS3, Vanilla JS ES6+, JSZip 3.10 (CDN), GitHub Pages

**Deploy target:** `C:\Users\Udacha\Documents\projects\aeo-generator\`

---

## File Structure

```
aeo-generator/
├── index.html          # Единственная страница: форма слева, вывод справа
├── css/
│   └── style.css       # Тёмная тема, фиолетовые акценты (как aeo-block.html)
├── js/
│   ├── generator.js    # Чистые функции генерации файлов (без DOM)
│   └── app.js          # UI: форма, табы, кнопки копирования, ZIP-скачивание
├── CLAUDE.md           # Принципы работы с проектом
└── robots.txt          # Для самого сайта-генератора (AEO для генератора)
```

---

## Task 1: Инициализация проекта

**Files:**
- Create: `aeo-generator/CLAUDE.md`
- Create: `aeo-generator/robots.txt`

- [ ] **Step 1: Создать директорию и инициализировать git**

```powershell
New-Item -ItemType Directory -Path "C:\Users\Udacha\Documents\projects\aeo-generator"
Set-Location "C:\Users\Udacha\Documents\projects\aeo-generator"
git init
```

Expected: `Initialized empty Git repository in .../aeo-generator/.git/`

- [ ] **Step 2: Создать CLAUDE.md**

Файл `aeo-generator/CLAUDE.md`:

```markdown
# CLAUDE.md

## Принципы

1. **Think Before Coding** — уточняй задачу, предлагай варианты.
2. **Simplicity First** — минимум кода, никаких лишних абстракций.
3. **Surgical Changes** — трогай только нужные файлы.
4. **Goal-Driven** — проверяй результат после каждой задачи.

## Структура

- `index.html` — вся разметка страницы
- `css/style.css` — стили (тёмная тема, фиолетовые акценты)
- `js/generator.js` — генерация файлов (чистые функции, без DOM)
- `js/app.js` — логика UI (форма, табы, ZIP-скачивание)

## Деплой

GitHub Pages: ветка `main`, корень репозитория.
```

- [ ] **Step 3: Создать robots.txt для самого сайта**

Файл `aeo-generator/robots.txt`:

```
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

Sitemap: https://prohar2f-pixel.github.io/aeo-generator/sitemap.xml
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md robots.txt
git commit -m "chore: init project"
```

---

## Task 2: Генератор файлов (generator.js)

**Files:**
- Create: `aeo-generator/js/generator.js`

Это сердце программы. Чистые функции — принимают объект `data`, возвращают строки.

```js
// Структура объекта data:
// {
//   url: "https://example.com",       // URL сайта (без финального слэша)
//   name: "Иван Петров",              // Имя / название компании
//   jobTitle: "Массажист",            // Должность / специальность
//   phone: "+79001234567",
//   email: "ivan@example.com",
//   telegram: "@ivan",                // Без @ тоже принимаем
//   city: "Москва",                   // Город / регион
//   services: [                       // Массив услуг
//     { name: "Массаж спины", price: "3000", currency: "RUB", duration: "60 минут" }
//   ],
//   faq: [                            // Массив вопросов
//     { q: "Сколько стоит?", a: "От 3000 ₽" }
//   ],
//   lang: "ru"                        // Язык сайта
// }
```

- [ ] **Step 1: Создать js/ директорию и файл generator.js с функцией generateRobots**

```js
// js/generator.js

function generateRobots(data) {
  const sitemapUrl = data.url.replace(/\/$/, '') + '/sitemap.xml';
  return `User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: YouBot
Allow: /

User-agent: Applebot-Extended
Allow: /

Sitemap: ${sitemapUrl}`;
}
```

- [ ] **Step 2: Добавить generateSitemap**

Дописать в конец `js/generator.js`:

```js
function generateSitemap(data) {
  const url = data.url.replace(/\/$/, '');
  const today = new Date().toISOString().split('T')[0];
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${url}/</loc>
    <lastmod>${today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>`;
}
```

- [ ] **Step 3: Добавить generateMetaTags**

Дописать в конец `js/generator.js`:

```js
function generateMetaTags(data) {
  const tgHandle = data.telegram
    ? (data.telegram.startsWith('@') ? data.telegram : '@' + data.telegram)
    : '';
  const tgUrl = tgHandle ? `https://t.me/${tgHandle.replace('@', '')}` : '';

  const lines = [
    `<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">`,
    `<meta name="author" content="${data.name}">`,
  ];
  if (tgUrl) lines.push(`<link rel="me" href="${tgUrl}">`);
  return lines.join('\n');
}
```

- [ ] **Step 4: Добавить generateJsonLd**

Дописать в конец `js/generator.js`:

```js
function generateJsonLd(data) {
  const url = data.url.replace(/\/$/, '');
  const tgHandle = data.telegram
    ? (data.telegram.startsWith('@') ? data.telegram : '@' + data.telegram)
    : '';
  const tgUrl = tgHandle ? `https://t.me/${tgHandle.replace('@', '')}` : '';

  const person = {
    "@type": "Person",
    "@id": url + "/#person",
    "name": data.name,
    "url": url + "/",
    "knowsLanguage": data.lang || "ru"
  };
  if (data.jobTitle) person.jobTitle = data.jobTitle;
  if (data.phone) person.telephone = data.phone;
  if (data.email) person.email = data.email;
  if (tgUrl) person.sameAs = [tgUrl];
  if (data.city) person.areaServed = data.city;

  if (data.services && data.services.length > 0) {
    person.offers = data.services.map(s => ({
      "@type": "Offer",
      "name": s.name,
      "price": s.price,
      "priceCurrency": s.currency || "RUB"
    }));
  }

  const webpage = {
    "@type": "WebPage",
    "@id": url + "/#webpage",
    "url": url + "/",
    "name": data.name + (data.jobTitle ? " — " + data.jobTitle : ""),
    "inLanguage": data.lang || "ru",
    "about": { "@id": url + "/#person" }
  };

  const graph = [person, webpage];

  if (data.services && data.services.length > 0) {
    data.services.forEach((s, i) => {
      graph.push({
        "@type": "Service",
        "@id": url + "/#service-" + i,
        "name": s.name,
        "provider": { "@id": url + "/#person" },
        "areaServed": data.city || "RU",
        "offers": {
          "@type": "Offer",
          "price": s.price,
          "priceCurrency": s.currency || "RUB",
          "availability": "https://schema.org/InStock"
        }
      });
    });
  }

  if (data.faq && data.faq.length > 0) {
    graph.push({
      "@type": "FAQPage",
      "mainEntity": data.faq.map(item => ({
        "@type": "Question",
        "name": item.q,
        "acceptedAnswer": { "@type": "Answer", "text": item.a }
      }))
    });
  }

  const schema = { "@context": "https://schema.org", "@graph": graph };
  return `<script type="application/ld+json">\n${JSON.stringify(schema, null, 2)}\n</script>`;
}
```

- [ ] **Step 5: Добавить generateFaqHtml**

Дописать в конец `js/generator.js`:

```js
function generateFaqHtml(data) {
  if (!data.faq || data.faq.length === 0) return '';
  const items = data.faq.map(item =>
    `  <details>\n    <summary>${item.q}</summary>\n    <p>${item.a}</p>\n  </details>`
  ).join('\n');
  return `<section id="faq">\n  <h2>Часто задаваемые вопросы</h2>\n${items}\n</section>`;
}
```

- [ ] **Step 6: Commit**

```bash
git add js/generator.js
git commit -m "feat: add AEO file generator functions"
```

---

## Task 3: UI логика (app.js)

**Files:**
- Create: `aeo-generator/js/app.js`

- [ ] **Step 1: Создать app.js — сбор данных из формы**

```js
// js/app.js

function collectFormData() {
  const getVal = id => document.getElementById(id).value.trim();

  const servicesRaw = getVal('services');
  const services = servicesRaw
    ? servicesRaw.split('\n').filter(Boolean).map(line => {
        const parts = line.split('|').map(s => s.trim());
        return { name: parts[0] || '', price: parts[1] || '0', currency: 'RUB', duration: parts[2] || '' };
      })
    : [];

  const faqRaw = getVal('faq');
  const faq = faqRaw
    ? faqRaw.split('\n').filter(Boolean).map(line => {
        const idx = line.indexOf('|');
        if (idx === -1) return { q: line, a: '' };
        return { q: line.slice(0, idx).trim(), a: line.slice(idx + 1).trim() };
      })
    : [];

  return {
    url: getVal('url').replace(/\/$/, ''),
    name: getVal('name'),
    jobTitle: getVal('jobTitle'),
    phone: getVal('phone'),
    email: getVal('email'),
    telegram: getVal('telegram'),
    city: getVal('city'),
    lang: getVal('lang') || 'ru',
    services,
    faq
  };
}
```

- [ ] **Step 2: Добавить функцию генерации и отображения результатов**

Дописать в конец `js/app.js`:

```js
function generate() {
  const data = collectFormData();

  if (!data.url || !data.name) {
    alert('Заполни минимум URL сайта и Имя / Название');
    return;
  }

  document.getElementById('out-robots').textContent = generateRobots(data);
  document.getElementById('out-sitemap').textContent = generateSitemap(data);
  document.getElementById('out-meta').textContent = generateMetaTags(data);
  document.getElementById('out-jsonld').textContent = generateJsonLd(data);
  document.getElementById('out-faq').textContent = generateFaqHtml(data);

  document.getElementById('output-section').classList.remove('hidden');
  switchTab('robots');
}
```

- [ ] **Step 3: Добавить переключение табов и копирование**

Дописать в конец `js/app.js`:

```js
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === name);
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('hidden', panel.dataset.panel !== name);
  });
}

function copyTab() {
  const activePanel = document.querySelector('.tab-panel:not(.hidden)');
  if (!activePanel) return;
  navigator.clipboard.writeText(activePanel.querySelector('pre').textContent)
    .then(() => {
      const btn = document.getElementById('copy-btn');
      btn.textContent = 'Скопировано!';
      setTimeout(() => { btn.textContent = 'Копировать'; }, 2000);
    });
}
```

- [ ] **Step 4: Добавить ZIP-скачивание**

Дописать в конец `js/app.js`:

```js
function downloadZip() {
  const data = collectFormData();
  const zip = new JSZip();

  zip.file('robots.txt', generateRobots(data));
  zip.file('sitemap.xml', generateSitemap(data));
  zip.file('meta-tags.html', generateMetaTags(data));
  zip.file('jsonld.html', generateJsonLd(data));
  const faqHtml = generateFaqHtml(data);
  if (faqHtml) zip.file('faq.html', faqHtml);

  zip.generateAsync({ type: 'blob' }).then(blob => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'aeo-package.zip';
    a.click();
    URL.revokeObjectURL(a.href);
  });
}
```

- [ ] **Step 5: Commit**

```bash
git add js/app.js
git commit -m "feat: add UI logic — form collection, tabs, copy, ZIP download"
```

---

## Task 4: Стили (style.css)

**Files:**
- Create: `aeo-generator/css/style.css`

- [ ] **Step 1: Создать style.css — базовые переменные и reset**

```css
/* css/style.css */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #080810;
  --surface: #0d0d1c;
  --border: rgba(168,85,247,.18);
  --border-hover: rgba(168,85,247,.45);
  --purple: #a855f7;
  --purple-dark: #7c3aed;
  --purple-light: #c084fc;
  --text: #f3f4f6;
  --muted: #6b7280;
  --green: #4ade80;
  --radius: 14px;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  min-height: 100vh;
  padding: 32px 24px;
}

.hidden { display: none !important; }
```

- [ ] **Step 2: Добавить layout и header**

Дописать в конец `css/style.css`:

```css
.wrap { max-width: 1200px; margin: 0 auto; }

header { text-align: center; margin-bottom: 48px; }
header .badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(168,85,247,.12); border: 1px solid rgba(168,85,247,.35);
  border-radius: 99px; padding: 5px 16px 5px 10px;
  font-size: .75rem; font-weight: 600; color: var(--purple-light);
  margin-bottom: 16px;
}
.badge-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--purple); box-shadow: 0 0 8px var(--purple); }
header h1 { font-size: 2.8rem; font-weight: 900; line-height: 1.1; margin-bottom: 12px; }
header h1 span {
  background: linear-gradient(90deg, #c084fc 0%, #818cf8 60%, #60a5fa 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
header p { color: var(--muted); font-size: .95rem; }

.layout { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: start; }
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
```

- [ ] **Step 3: Добавить стили формы**

Дописать в конец `css/style.css`:

```css
.form-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 28px;
}
.form-card h2 { font-size: 1rem; font-weight: 700; margin-bottom: 20px; color: var(--purple-light); }

.field { margin-bottom: 16px; }
.field label { display: block; font-size: .78rem; font-weight: 600; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .04em; }
.field input, .field textarea, .field select {
  width: 100%; background: rgba(255,255,255,.04); border: 1px solid var(--border);
  border-radius: 10px; padding: 10px 14px;
  color: var(--text); font-family: inherit; font-size: .88rem;
  transition: border-color .2s;
  outline: none;
}
.field input:focus, .field textarea:focus, .field select:focus { border-color: var(--purple); }
.field textarea { resize: vertical; min-height: 80px; }
.field .hint { font-size: .72rem; color: var(--muted); margin-top: 4px; }

.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.btn-generate {
  width: 100%; padding: 16px;
  background: linear-gradient(135deg, var(--purple-dark), var(--purple));
  border: none; border-radius: 14px;
  color: #fff; font-family: inherit; font-size: 1rem; font-weight: 800;
  cursor: pointer; margin-top: 8px;
  box-shadow: 0 0 30px rgba(139,92,246,.4);
  transition: transform .2s, box-shadow .3s;
}
.btn-generate:hover { transform: translateY(-2px); box-shadow: 0 0 50px rgba(168,85,247,.65); }
```

- [ ] **Step 4: Добавить стили вывода и табов**

Дописать в конец `css/style.css`:

```css
.output-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 28px; position: sticky; top: 24px;
}
.output-card h2 { font-size: 1rem; font-weight: 700; margin-bottom: 16px; color: var(--purple-light); }

.tabs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
.tab-btn {
  background: rgba(255,255,255,.05); border: 1px solid var(--border);
  border-radius: 8px; padding: 6px 14px;
  color: var(--muted); font-family: inherit; font-size: .78rem; font-weight: 600;
  cursor: pointer; transition: all .2s;
}
.tab-btn.active { background: rgba(168,85,247,.15); border-color: var(--purple); color: var(--purple-light); }
.tab-btn:hover:not(.active) { border-color: var(--border-hover); color: var(--text); }

.tab-panel pre {
  background: rgba(0,0,0,.3); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px;
  font-size: .78rem; line-height: 1.7; overflow-x: auto;
  white-space: pre-wrap; word-break: break-all;
  max-height: 360px; overflow-y: auto;
  color: #d1d5db;
}

.output-actions { display: flex; gap: 10px; margin-top: 14px; }
.btn-copy, .btn-zip {
  flex: 1; padding: 12px;
  border-radius: 10px; border: 1px solid var(--border);
  font-family: inherit; font-size: .85rem; font-weight: 700;
  cursor: pointer; transition: all .2s;
}
.btn-copy { background: rgba(168,85,247,.1); color: var(--purple-light); }
.btn-copy:hover { background: rgba(168,85,247,.2); border-color: var(--purple); }
.btn-zip {
  background: linear-gradient(135deg, var(--purple-dark), var(--purple));
  color: #fff; border: none;
  box-shadow: 0 0 20px rgba(139,92,246,.3);
}
.btn-zip:hover { box-shadow: 0 0 35px rgba(168,85,247,.55); transform: translateY(-1px); }
```

- [ ] **Step 5: Commit**

```bash
git add css/style.css
git commit -m "feat: add dark theme styles"
```

---

## Task 5: Разметка (index.html)

**Files:**
- Create: `aeo-generator/index.html`

- [ ] **Step 1: Создать index.html**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AEO Generator — сделай сайт видимым для ИИ</title>
<meta name="description" content="Генератор AEO-пакета: robots.txt, sitemap.xml, JSON-LD схема, мета-теги и FAQ для статического сайта. Скачай готовые файлы за 2 минуты.">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<div class="wrap">

  <header>
    <div class="badge"><span class="badge-dot"></span>AEO Generator · 2026</div>
    <h1>Сделай сайт видимым<br><span>для ChatGPT, Perplexity и Claude</span></h1>
    <p>Введи данные бизнеса — получи готовые файлы для AEO-оптимизации</p>
  </header>

  <div class="layout">

    <!-- ФОРМА -->
    <div class="form-card">
      <h2>Данные сайта</h2>

      <div class="field">
        <label>URL сайта *</label>
        <input id="url" type="url" placeholder="https://example.com">
      </div>

      <div class="row2">
        <div class="field">
          <label>Имя / Название *</label>
          <input id="name" type="text" placeholder="Иван Петров">
        </div>
        <div class="field">
          <label>Специальность</label>
          <input id="jobTitle" type="text" placeholder="Массажист">
        </div>
      </div>

      <div class="row2">
        <div class="field">
          <label>Телефон</label>
          <input id="phone" type="tel" placeholder="+79001234567">
        </div>
        <div class="field">
          <label>Email</label>
          <input id="email" type="email" placeholder="ivan@example.com">
        </div>
      </div>

      <div class="row2">
        <div class="field">
          <label>Telegram</label>
          <input id="telegram" type="text" placeholder="@username">
        </div>
        <div class="field">
          <label>Город</label>
          <input id="city" type="text" placeholder="Москва">
        </div>
      </div>

      <div class="field">
        <label>Услуги</label>
        <textarea id="services" placeholder="Массаж спины | 3000 | 60 минут&#10;Массаж шеи | 2000 | 30 минут"></textarea>
        <div class="hint">Формат: Название | Цена | Длительность (каждая услуга с новой строки)</div>
      </div>

      <div class="field">
        <label>FAQ — вопросы и ответы</label>
        <textarea id="faq" placeholder="Сколько стоит сеанс? | От 2000 ₽, зависит от длительности&#10;Как записаться? | Напишите в Telegram"></textarea>
        <div class="hint">Формат: Вопрос | Ответ (каждая пара с новой строки)</div>
      </div>

      <div class="field">
        <label>Язык сайта</label>
        <select id="lang">
          <option value="ru">Русский (ru)</option>
          <option value="en">English (en)</option>
        </select>
      </div>

      <button class="btn-generate" onclick="generate()">Сгенерировать AEO-пакет</button>
    </div>

    <!-- ВЫВОД -->
    <div id="output-section" class="output-card hidden">
      <h2>Готовые файлы</h2>

      <div class="tabs">
        <button class="tab-btn active" data-tab="robots" onclick="switchTab('robots')">robots.txt</button>
        <button class="tab-btn" data-tab="sitemap" onclick="switchTab('sitemap')">sitemap.xml</button>
        <button class="tab-btn" data-tab="meta" onclick="switchTab('meta')">meta-теги</button>
        <button class="tab-btn" data-tab="jsonld" onclick="switchTab('jsonld')">JSON-LD</button>
        <button class="tab-btn" data-tab="faq" onclick="switchTab('faq')">FAQ HTML</button>
      </div>

      <div class="tab-panel" data-panel="robots"><pre id="out-robots"></pre></div>
      <div class="tab-panel hidden" data-panel="sitemap"><pre id="out-sitemap"></pre></div>
      <div class="tab-panel hidden" data-panel="meta"><pre id="out-meta"></pre></div>
      <div class="tab-panel hidden" data-panel="jsonld"><pre id="out-jsonld"></pre></div>
      <div class="tab-panel hidden" data-panel="faq"><pre id="out-faq"></pre></div>

      <div class="output-actions">
        <button class="btn-copy" id="copy-btn" onclick="copyTab()">Копировать</button>
        <button class="btn-zip" onclick="downloadZip()">⬇ Скачать всё (ZIP)</button>
      </div>
    </div>

  </div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="js/generator.js"></script>
<script src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Проверить в браузере**

Открыть `index.html` в браузере двойным кликом.
Проверить:
- Форма отображается корректно
- После нажатия "Сгенерировать" появляется блок с результатами
- Переключение табов работает
- Кнопка "Копировать" копирует содержимое активного таба
- Кнопка "Скачать всё (ZIP)" скачивает архив с файлами

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add main page layout and form"
```

---

## Task 6: Деплой на GitHub Pages

**Files:** нет новых файлов, только GitHub actions

- [ ] **Step 1: Создать репозиторий на GitHub**

На GitHub.com создать новый публичный репозиторий с именем `aeo-generator`.

- [ ] **Step 2: Добавить remote и запушить**

```bash
git remote add origin https://github.com/prohar2f-pixel/aeo-generator.git
git branch -M main
git push -u origin main
```

- [ ] **Step 3: Включить GitHub Pages**

В Settings → Pages → Source → Deploy from a branch → `main` / `/ (root)` → Save.

- [ ] **Step 4: Проверить деплой**

Через 1–2 минуты открыть `https://prohar2f-pixel.github.io/aeo-generator/`.

Проверить:
- Сайт открывается
- Генератор работает
- ZIP скачивается

- [ ] **Step 5: Уведомить о результате**

Сообщить пользователю URL сайта и URL репозитория.

---

## Self-Review

**Spec coverage:**
- ✅ Форма ввода данных бизнеса
- ✅ Генерация robots.txt с правилами для всех ИИ-ботов
- ✅ Генерация sitemap.xml
- ✅ Генерация мета-тегов
- ✅ Генерация JSON-LD (@graph: Person + WebPage + Service[] + FAQPage)
- ✅ Генерация FAQ HTML
- ✅ Копирование в буфер обмена
- ✅ Скачивание ZIP-архива
- ✅ Деплой на GitHub Pages
- ✅ CLAUDE.md в новом проекте
- ✅ robots.txt для самого сайта-генератора

**Placeholder scan:** Нет TBD, TODO, "fill in details". Все шаги содержат реальный код.

**Type consistency:** Объект `data` определён в Task 2 Step 1, используется идентично во всех функциях generator.js и в app.js.
