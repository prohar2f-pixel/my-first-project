# SEO Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить к AEO-генератору вторую страницу `seo.html`, которая по тому же сценарию (вставил URL → AI-анализ → автозаполнение формы) выдаёт полный пакет SEO-файлов в ZIP.

**Architecture:** Общие функции формы/анализатора/счётчика выносятся из `app.js` в новый `js/shared.js`, который подключают обе страницы. SEO-страница получает свои `js/seo-generator.js` (чистые функции) и `js/seo-app.js` (UI). Переключатель AEO/SEO — две ссылки в шапке. Без сборщиков и npm.

**Tech Stack:** HTML5, CSS3, Vanilla JS ES6+, JSZip 3.10 (CDN), Node.js (только для проверки чистых функций), GitHub Pages.

**Working directory:** `C:\Users\Udacha\Documents\projects\aeo-generator\`

---

## File Structure

```
aeo-generator/
├── index.html          # МЕНЯЕТСЯ: + переключатель, + подключение shared.js
├── seo.html            # НОВЫЙ: SEO-страница
├── css/
│   └── style.css       # МЕНЯЕТСЯ: + стили .mode-switch / .mode-tab
└── js/
    ├── generator.js    # без изменений (AEO-генераторы)
    ├── shared.js       # НОВЫЙ: общие функции (вынос из app.js)
    ├── app.js          # МЕНЯЕТСЯ: остаётся только AEO generate()/downloadZip()
    ├── seo-generator.js # НОВЫЙ: чистые функции SEO-файлов
    └── seo-app.js      # НОВЫЙ: SEO generate()/downloadZip()
```

**Объект `data`** (возвращает `collectFormData`, не меняется):
```js
{ url, name, jobTitle, phone, email, telegram, city, lang, services: [{name, price, currency, duration}], faq: [{q, a}] }
```

---

## Task 1: Вынести общие функции в shared.js

Переносим из `app.js` всё, что не относится к генерации AEO-файлов, в новый `js/shared.js`. После этого `app.js` будет подключаться ПОСЛЕ `shared.js` и использовать его функции.

**Files:**
- Create: `js/shared.js`
- Modify: `js/app.js`
- Modify: `index.html`

- [ ] **Step 1: Создать `js/shared.js`**

Скопировать в новый файл `js/shared.js` (это строки 1–148 текущего `app.js` — константы, счётчик, лид, анализатор, сбор формы, табы, копирование):

```js
// shared.js — общие функции для AEO и SEO страниц

const WORKER_URL = 'https://aeo-analyzer.prohar2f.workers.dev';
const CONTACT_URL = 'https://prohar-contact-form.prohar2f.workers.dev';
const COUNTER_URL = 'https://api.countapi.xyz/hit/aeo-gen-prohar/uses';
const COUNTER_BASE = 47;

async function loadCounter() {
  try {
    const res = await fetch('https://api.countapi.xyz/get/aeo-gen-prohar/uses');
    const json = await res.json();
    document.getElementById('counter-badge').textContent = COUNTER_BASE + (json.value || 0);
  } catch {
    document.getElementById('counter-badge').textContent = COUNTER_BASE;
  }
}

async function incrementCounter() {
  try {
    const res = await fetch(COUNTER_URL);
    const json = await res.json();
    document.getElementById('counter-badge').textContent = COUNTER_BASE + (json.value || 0);
  } catch { /* тихо игнорируем */ }
}

async function submitLead() {
  const email = document.getElementById('lead-email').value.trim();
  if (!email) return;
  const btn = document.getElementById('lead-btn');
  const status = document.getElementById('lead-status');
  const url = document.getElementById('url').value.trim();
  btn.disabled = true;
  btn.textContent = '...';
  try {
    await fetch(CONTACT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Generator Lead',
        phone: email,
        email,
        service: 'AEO/SEO-оптимизация: 5 000 ₽ (акция)',
        comment: `Пользователь сгенерировал пакет${url ? ' для: ' + url : ''}`,
      }),
    });
    status.textContent = '✓ Отправлено — свяжемся скоро';
    status.style.color = '#4ade80';
    document.getElementById('lead-email').value = '';
  } catch {
    status.textContent = '✗ Не получилось — напиши в Telegram @alex_prohar';
    status.style.color = '#f87171';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Отправить';
  }
}

loadCounter();

async function analyzeUrl() {
  const url = document.getElementById('url').value.trim();
  if (!url || !url.startsWith('http')) {
    alert('Введи корректный URL сайта (начинается с https://)');
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  const status = document.getElementById('analyze-status');

  btn.disabled = true;
  status.className = 'hint loading';
  status.textContent = '⏳ Анализирую сайт...';

  try {
    const res = await fetch(WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    const json = await res.json();

    if (!json.ok || !json.data) {
      throw new Error((json.error || 'unknown_error') + (json.detail ? ': ' + json.detail : ''));
    }

    const d = json.data;
    const setVal = (id, val) => { if (val) document.getElementById(id).value = val; };

    setVal('name', d.name);
    setVal('jobTitle', d.jobTitle);
    setVal('phone', d.phone);
    setVal('email', d.email);
    setVal('telegram', d.telegram);
    setVal('city', d.city);

    if (d.services && d.services.length > 0) {
      document.getElementById('services').value = d.services
        .map(s => `${s.name} | ${s.price} | `)
        .join('\n');
    }

    if (d.faq && d.faq.length > 0) {
      document.getElementById('faq').value = d.faq
        .map(f => `${f.q} | ${f.a}`)
        .join('\n');
    }

    status.className = 'hint success';
    status.textContent = '✓ Форма заполнена автоматически — проверь и исправь если нужно';
  } catch (err) {
    status.className = 'hint error';
    status.textContent = '✗ Ошибка: ' + err.message;
  } finally {
    btn.disabled = false;
  }
}

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

- [ ] **Step 2: Удалить перенесённые функции из `js/app.js`**

После переноса `js/app.js` должен содержать ТОЛЬКО AEO-`generate()` и AEO-`downloadZip()`. Заменить всё содержимое `js/app.js` на:

```js
// app.js — AEO-специфичная логика (общие функции в shared.js)

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
  incrementCounter();
}

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

- [ ] **Step 3: Подключить `shared.js` в `index.html`**

В `index.html` найти блок подключения скриптов в конце `<body>`:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="js/generator.js"></script>
<script src="js/app.js"></script>
```

Заменить на (добавить `shared.js` между `generator.js` и `app.js`):

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="js/generator.js"></script>
<script src="js/shared.js"></script>
<script src="js/app.js"></script>
```

- [ ] **Step 4: Проверить AEO-страницу в браузере**

Открыть `index.html` двойным кликом. Заполнить URL = `https://example.com`, Имя = `Тест`. Нажать «Сгенерировать AEO-пакет».
Expected: появляются 5 вкладок с содержимым, «Копировать» работает, «Скачать всё (ZIP)» качает `aeo-package.zip`. В консоли браузера (F12) нет ошибок `is not defined`.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Udacha/Documents/projects/aeo-generator"
git add js/shared.js js/app.js index.html
git commit -m "refactor: extract shared form/analyzer logic into shared.js"
```

---

## Task 2: SEO-генераторы (seo-generator.js)

Чистые функции — принимают `data`, возвращают строки. Без DOM. Проверяются через Node.

**Files:**
- Create: `js/seo-generator.js`

- [ ] **Step 1: Создать `js/seo-generator.js` с `buildTitle`/`buildDescription` и `generateTitleDesc`**

```js
// seo-generator.js — чистые функции генерации SEO-файлов. Без DOM.

function buildTitle(data) {
  let t = data.name || 'Сайт';
  if (data.jobTitle) t += ' — ' + data.jobTitle;
  if (data.city) t += ' в ' + data.city;
  t += ' | Цены и запись';
  return t.length > 60 ? t.slice(0, 57).trimEnd() + '...' : t;
}

function buildDescription(data) {
  const parts = [];
  if (data.jobTitle) parts.push(data.jobTitle);
  if (data.name) parts.push(data.name);
  if (data.city) parts.push('в городе ' + data.city);
  let d = parts.join(' ');
  if (data.services && data.services.length > 0) {
    d += '. ' + data.services.map(s => s.name).filter(Boolean).join(', ');
  }
  if (data.phone) d += '. Запись по телефону ' + data.phone;
  d = d.trim();
  return d.length > 160 ? d.slice(0, 157).trimEnd() + '...' : d;
}

function generateTitleDesc(data) {
  return `<title>${buildTitle(data)}</title>\n<meta name="description" content="${buildDescription(data)}">`;
}
```

- [ ] **Step 2: Проверить `generateTitleDesc` через Node**

Run:
```bash
cd "C:/Users/Udacha/Documents/projects/aeo-generator"
node -e "$(cat js/seo-generator.js); console.log(generateTitleDesc({name:'Иван Петров',jobTitle:'Массажист',city:'Москва',phone:'+79001234567',services:[{name:'Массаж спины'}]}))"
```
Expected:
```
<title>Иван Петров — Массажист в Москва | Цены и запись</title>
<meta name="description" content="Массажист Иван Петров в городе Москва. Массаж спины. Запись по телефону +79001234567">
```

- [ ] **Step 3: Добавить `generateOgTwitter`**

Дописать в конец `js/seo-generator.js`:

```js
function generateOgTwitter(data) {
  const url = (data.url || '').replace(/\/$/, '');
  const title = buildTitle(data);
  const desc = buildDescription(data);
  const img = url + '/og-image.jpg';
  return [
    `<meta property="og:type" content="website">`,
    `<meta property="og:title" content="${title}">`,
    `<meta property="og:description" content="${desc}">`,
    `<meta property="og:url" content="${url}/">`,
    `<meta property="og:image" content="${img}">`,
    `<meta property="og:locale" content="${(data.lang || 'ru') === 'ru' ? 'ru_RU' : 'en_US'}">`,
    `<meta name="twitter:card" content="summary_large_image">`,
    `<meta name="twitter:title" content="${title}">`,
    `<meta name="twitter:description" content="${desc}">`,
    `<meta name="twitter:image" content="${img}">`,
  ].join('\n');
}
```

- [ ] **Step 4: Проверить `generateOgTwitter` через Node**

Run:
```bash
node -e "$(cat js/seo-generator.js); console.log(generateOgTwitter({name:'Иван',jobTitle:'Массажист',city:'Москва',url:'https://example.com/'}))"
```
Expected: 10 строк мета-тегов, в `og:url` = `https://example.com/`, в `og:image` = `https://example.com/og-image.jpg`, `og:locale` = `ru_RU`.

- [ ] **Step 5: Добавить `generateLocalBusiness`**

Дописать в конец `js/seo-generator.js`:

```js
function generateLocalBusiness(data) {
  const url = (data.url || '').replace(/\/$/, '');
  const tgHandle = data.telegram
    ? (data.telegram.startsWith('@') ? data.telegram : '@' + data.telegram)
    : '';
  const tgUrl = tgHandle ? `https://t.me/${tgHandle.replace('@', '')}` : '';

  const biz = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": data.name,
    "url": url + "/"
  };
  if (data.phone) biz.telephone = data.phone;
  if (data.email) biz.email = data.email;
  if (data.city) {
    biz.address = { "@type": "PostalAddress", "addressLocality": data.city, "addressCountry": "RU" };
    biz.areaServed = data.city;
  }
  if (data.services && data.services.length > 0) {
    const prices = data.services.map(s => parseInt(s.price, 10)).filter(n => n > 0);
    if (prices.length > 0) {
      const min = Math.min(...prices), max = Math.max(...prices);
      biz.priceRange = min === max ? `${min} ₽` : `${min}–${max} ₽`;
    }
  }
  if (tgUrl) biz.sameAs = [tgUrl];

  return `<script type="application/ld+json">\n${JSON.stringify(biz, null, 2)}\n</script>`;
}
```

- [ ] **Step 6: Проверить `generateLocalBusiness` через Node**

Run:
```bash
node -e "$(cat js/seo-generator.js); console.log(generateLocalBusiness({name:'Иван',url:'https://example.com',phone:'+79001234567',city:'Москва',services:[{name:'A',price:'2000'},{name:'B',price:'3000'}],telegram:'ivan'}))"
```
Expected: валидный JSON внутри `<script type="application/ld+json">`, `priceRange` = `"2000–3000 ₽"`, `sameAs` = `["https://t.me/ivan"]`, `address.addressLocality` = `"Москва"`.

- [ ] **Step 7: Добавить `generateSeoChecklist`**

Дописать в конец `js/seo-generator.js`:

```js
function generateSeoChecklist(data) {
  const site = (data.url || 'твой сайт').replace(/\/$/, '');
  return `SEO-ЧЕКЛИСТ для ${site}
========================================

УЖЕ ГОТОВО (вставь файлы из пакета в <head> страницы):
[x] Title и meta description — из файла title-description.html
[x] Open Graph и Twitter Card — из файла og-twitter.html
[x] LocalBusiness разметка — из файла localbusiness.html

ОСТАЛОСЬ СДЕЛАТЬ РУКАМИ:
[ ] Один <h1> на странице с главным ключевым словом
[ ] Тег alt у всех картинок (описание словами, что на фото)
[ ] Картинка для соцсетей og-image.jpg размером 1200x630 px в корне сайта
[ ] Добавить в LocalBusiness точный адрес и часы работы
[ ] Сжать картинки и проверить скорость на PageSpeed Insights (pagespeed.web.dev)
[ ] Поставить внутренние ссылки между страницами сайта
[ ] Зарегистрировать сайт в Яндекс.Вебмастер (webmaster.yandex.ru)
[ ] Зарегистрировать сайт в Google Search Console (search.google.com/search-console)
`;
}
```

- [ ] **Step 8: Проверить `generateSeoChecklist` через Node**

Run:
```bash
node -e "$(cat js/seo-generator.js); console.log(generateSeoChecklist({url:'https://example.com/'}))"
```
Expected: текст чеклиста, в заголовке `https://example.com`, три пункта `[x]` и восемь `[ ]`.

- [ ] **Step 9: Commit**

```bash
git add js/seo-generator.js
git commit -m "feat: add SEO file generator functions"
```

---

## Task 3: SEO UI-логика (seo-app.js)

**Files:**
- Create: `js/seo-app.js`

- [ ] **Step 1: Создать `js/seo-app.js`**

```js
// seo-app.js — SEO-специфичная логика (общие функции в shared.js)

function generate() {
  const data = collectFormData();

  if (!data.url || !data.name) {
    alert('Заполни минимум URL сайта и Имя / Название');
    return;
  }

  document.getElementById('out-titledesc').textContent = generateTitleDesc(data);
  document.getElementById('out-og').textContent = generateOgTwitter(data);
  document.getElementById('out-localbiz').textContent = generateLocalBusiness(data);
  document.getElementById('out-checklist').textContent = generateSeoChecklist(data);

  document.getElementById('output-section').classList.remove('hidden');
  switchTab('titledesc');
  incrementCounter();
}

function downloadZip() {
  const data = collectFormData();
  const zip = new JSZip();

  zip.file('title-description.html', generateTitleDesc(data));
  zip.file('og-twitter.html', generateOgTwitter(data));
  zip.file('localbusiness.html', generateLocalBusiness(data));
  zip.file('seo-checklist.txt', generateSeoChecklist(data));

  zip.generateAsync({ type: 'blob' }).then(blob => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'seo-package.zip';
    a.click();
    URL.revokeObjectURL(a.href);
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add js/seo-app.js
git commit -m "feat: add SEO UI logic — generate and ZIP download"
```

---

## Task 4: Переключатель AEO/SEO — стили

**Files:**
- Modify: `css/style.css`

- [ ] **Step 1: Добавить стили переключателя в конец `css/style.css`**

```css
/* Переключатель AEO / SEO */
.mode-switch {
  display: flex; gap: 6px; justify-content: center;
  margin-bottom: 24px;
}
.mode-tab {
  padding: 8px 24px; border-radius: 99px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.04);
  color: var(--muted); text-decoration: none;
  font-weight: 700; font-size: .85rem;
  transition: all .2s;
}
.mode-tab:hover { border-color: var(--border-hover); color: var(--text); }
.mode-tab.active {
  background: linear-gradient(135deg, var(--purple-dark), var(--purple));
  color: #fff; border-color: transparent;
  box-shadow: 0 0 20px rgba(139,92,246,.4);
}
```

- [ ] **Step 2: Добавить переключатель в `index.html`**

В `index.html` сразу после открытия `<div class="wrap">` (перед `<header>`) вставить:

```html
  <nav class="mode-switch">
    <a href="index.html" class="mode-tab active">AEO · для ИИ</a>
    <a href="seo.html" class="mode-tab">SEO · для Google</a>
  </nav>
```

- [ ] **Step 3: Проверить в браузере**

Открыть `index.html`. Expected: вверху по центру две пилюли, активна «AEO · для ИИ» (фиолетовая). Клик по «SEO · для Google» ведёт на `seo.html` (пока 404/пусто — нормально, создаём в Task 5).

- [ ] **Step 4: Commit**

```bash
git add css/style.css index.html
git commit -m "feat: add AEO/SEO mode switch"
```

---

## Task 5: SEO-страница (seo.html)

**Files:**
- Create: `seo.html`

- [ ] **Step 1: Создать `seo.html`**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO Generator — сделай сайт первым в Google и Яндекс</title>
<meta name="description" content="Генератор SEO-пакета: title, description, Open Graph, LocalBusiness Schema и чеклист для статического сайта. Бесплатный органический трафик за 2 минуты.">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="author" content="Александр Прохоров">
<link rel="canonical" href="https://aeo.aiprohar.ru/seo.html">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<div class="wrap">

  <nav class="mode-switch">
    <a href="index.html" class="mode-tab">AEO · для ИИ</a>
    <a href="seo.html" class="mode-tab active">SEO · для Google</a>
  </nav>

  <header>
    <div class="badge"><span class="badge-dot"></span>Уже оптимизировано: <span id="counter-badge">...</span> сайтов</div>
    <h1>Сделай сайт первым<br><span>в Google и Яндекс</span></h1>
    <p>Введи данные бизнеса — получи готовые файлы для SEO-оптимизации</p>
  </header>

  <!-- КАК ЭТО РАБОТАЕТ -->
  <div class="how-it-works">
    <div class="how-step">
      <div class="how-num">1</div>
      <div class="how-icon">🔗</div>
      <div class="how-text">
        <strong>Введи URL сайта</strong>
        <span>Нажми «Анализировать» — ИИ изучит сайт и заполнит форму автоматически</span>
      </div>
    </div>
    <div class="how-arrow">→</div>
    <div class="how-step">
      <div class="how-num">2</div>
      <div class="how-icon">✏️</div>
      <div class="how-text">
        <strong>Проверь данные</strong>
        <span>Исправь если нужно: имя, услуги, FAQ — всё уже заполнено за тебя</span>
      </div>
    </div>
    <div class="how-arrow">→</div>
    <div class="how-step">
      <div class="how-num">3</div>
      <div class="how-icon">⬇️</div>
      <div class="how-text">
        <strong>Скачай ZIP-архив</strong>
        <span>Положи файлы на сайт — Google и Яндекс поднимут тебя в выдаче</span>
      </div>
    </div>
  </div>

  <div class="layout">

    <!-- ФОРМА -->
    <div class="form-card">
      <h2>Данные сайта</h2>

      <div class="field">
        <label>URL сайта *</label>
        <div class="url-row">
          <input id="url" type="url" placeholder="https://example.com">
          <button class="btn-analyze" id="analyzeBtn" onclick="analyzeUrl()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            Анализировать
          </button>
        </div>
        <div class="hint" id="analyze-status"></div>
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

      <button class="btn-generate" onclick="generate()">Сгенерировать SEO-пакет</button>
    </div>

    <!-- ВЫВОД -->
    <div id="output-section" class="output-card hidden">
      <h2>Готовые файлы</h2>

      <div class="tabs">
        <button class="tab-btn active" data-tab="titledesc" onclick="switchTab('titledesc')">Title + Description</button>
        <button class="tab-btn" data-tab="og" onclick="switchTab('og')">OG + Twitter</button>
        <button class="tab-btn" data-tab="localbiz" onclick="switchTab('localbiz')">LocalBusiness</button>
        <button class="tab-btn" data-tab="checklist" onclick="switchTab('checklist')">Чеклист</button>
      </div>

      <div class="tab-panel" data-panel="titledesc"><pre id="out-titledesc"></pre></div>
      <div class="tab-panel hidden" data-panel="og"><pre id="out-og"></pre></div>
      <div class="tab-panel hidden" data-panel="localbiz"><pre id="out-localbiz"></pre></div>
      <div class="tab-panel hidden" data-panel="checklist"><pre id="out-checklist"></pre></div>

      <div class="output-actions">
        <button class="btn-copy" id="copy-btn" onclick="copyTab()">Копировать</button>
        <button class="btn-zip" onclick="downloadZip()">⬇ Скачать всё (ZIP)</button>
      </div>

      <div class="email-capture" id="email-capture">
        <p class="email-caption">Хочешь чтобы мы настроили SEO за тебя? Оставь email — свяжемся:</p>
        <div class="email-row">
          <input id="lead-email" type="email" placeholder="твой@email.com">
          <button class="btn-lead" id="lead-btn" onclick="submitLead()">Отправить</button>
        </div>
        <div id="lead-status" class="hint"></div>
      </div>
    </div>

  </div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="js/seo-generator.js"></script>
<script src="js/shared.js"></script>
<script src="js/seo-app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Проверить SEO-страницу в браузере**

Открыть `seo.html` двойным кликом. Заполнить URL = `https://example.com`, Имя = `Иван Петров`, Специальность = `Массажист`, Город = `Москва`, Услуги = `Массаж спины | 3000 | 60 минут`. Нажать «Сгенерировать SEO-пакет».
Expected:
- Появляется блок с 4 вкладками: Title + Description, OG + Twitter, LocalBusiness, Чеклист.
- В первой вкладке виден `<title>...</title>` и meta description.
- Переключение вкладок работает, «Копировать» копирует активную вкладку.
- «Скачать всё (ZIP)» качает `seo-package.zip` с 4 файлами.
- Переключатель вверху: активна «SEO · для Google», клик по «AEO · для ИИ» ведёт на `index.html`.
- В консоли (F12) нет ошибок.

- [ ] **Step 3: Commit**

```bash
git add seo.html
git commit -m "feat: add SEO generator page"
```

---

## Task 6: Деплой

**Files:** нет новых файлов.

- [ ] **Step 1: Push в main**

```bash
cd "C:/Users/Udacha/Documents/projects/aeo-generator"
git push origin main
```

- [ ] **Step 2: Проверить на проде**

Через 1–2 минуты открыть `https://aeo.aiprohar.ru/seo.html`.
Expected: SEO-страница открывается, генератор работает, ZIP качается, переключатель ведёт на `https://aeo.aiprohar.ru/` (AEO).

- [ ] **Step 3: Уведомить пользователя**

Сообщить: SEO-страница доступна по `https://aeo.aiprohar.ru/seo.html`, переключатель связывает обе страницы.

---

## Self-Review

**Spec coverage:**
- ✅ Отдельная страница `seo.html` (Task 5)
- ✅ Общий код в `shared.js`, рефакторинг `app.js` без поломки AEO (Task 1)
- ✅ Переключатель AEO/SEO ссылками (Task 4 + Task 5)
- ✅ `generateTitleDesc` — Title + Description с длиной (Task 2)
- ✅ `generateOgTwitter` — OG + Twitter Card (Task 2)
- ✅ `generateLocalBusiness` — LocalBusiness JSON-LD (Task 2)
- ✅ `generateSeoChecklist` — чеклист с галочками (Task 2)
- ✅ `seo-app.js` — generate() + downloadZip() с 4 файлами, архив `seo-package.zip` (Task 3)
- ✅ Стили `.mode-switch`/`.mode-tab` (Task 4)
- ✅ Деплой на GitHub Pages (Task 6)

**Placeholder scan:** Нет TBD/TODO. Весь код приведён полностью.

**Type consistency:** Объект `data` идентичен во всех функциях. ID вкладок (`out-titledesc`, `out-og`, `out-localbiz`, `out-checklist`) и имена табов (`titledesc`, `og`, `localbiz`, `checklist`) совпадают между `seo.html` (Task 5) и `seo-app.js` (Task 3). Функции `buildTitle`/`buildDescription` определены в Task 2 Step 1 до использования в Step 3/5. Имена `generate`/`downloadZip` намеренно совпадают с AEO — конфликта нет, т.к. страницы подключают разные UI-файлы.
```
