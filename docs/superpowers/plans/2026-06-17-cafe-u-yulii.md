# Cafe U Yulii — Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file HTML prototype landing page for café «У Юлии» (Uzbek halal cuisine) to present to the client.

**Architecture:** One self-contained `drafts/cafe-u-yulii.html` file with embedded CSS and JS — no build tools, no external dependencies except Google Fonts CDN and Unsplash image URLs. Page is split into 8 sections built task by task, each committed independently.

**Tech Stack:** Vanilla HTML5, CSS3 (Variables + Grid + Flexbox), Vanilla JS (ES6), Google Fonts CDN (Playfair Display + Inter), Unsplash direct URLs.

## Global Constraints

- Single file: `drafts/cafe-u-yulii.html` — CSS in `<style>`, JS in `<script>`, no external files
- No JS frameworks, no CSS frameworks (no Bootstrap, no Tailwind)
- Halal concept — no alcohol, no pork anywhere in copy
- Real client data must be used (see Data section below)
- Mobile breakpoint: 768px — all sections must stack to single column below it
- Commit format: `[agent] feat: cafe-u-yulii — <section name>`
- Working directory: `C:\Users\Administrator\projects\my-first-project`

## Real Client Data (use verbatim)

```
Название: Кафе «У Юлии»
Концепция: Узбекская кухня. Халяль.
Адрес: М/О, Беседы, Деревня Мильково, вл1с2
Телефон: +7 (925) 27-545-27
WhatsApp: https://wa.me/79055537530
Instagram: https://www.instagram.com/chaihana.namangan
Рейтинги: Яндекс 4.4 / Google 4.3 / 2GIS 5.0
```

## Menu Items (placeholder prices — client will update)

```
Плов по-узбекски       — 350 ₽
Лагман домашний        — 320 ₽
Шурпа                  — 290 ₽
Манты                  — 300 ₽
Шашлык из баранины     — 550 ₽
Самса                  — 150 ₽
```

## Color Palette (CSS Variables)

```css
--color-dark:   #3D1A0E;
--color-cream:  #F5F0E8;
--color-gold:   #C8A96E;
--color-white:  #FFFFFF;
--color-overlay: rgba(30, 10, 5, 0.65);
```

## Unsplash Image URLs

```
Hero bg:   https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1920&q=80
Plov:      https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&q=80
Lagman:    https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?w=400&q=80
Shurpa:    https://images.unsplash.com/photo-1547592180-85f173990554?w=400&q=80
Manti:     https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&q=80
Shashlik:  https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&q=80
Samsa:     https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&q=80
Banquet:   https://images.unsplash.com/photo-1527529482837-4698179dc6ce?w=600&q=80
Delivery:  https://images.unsplash.com/photo-1526367790999-0150786686a2?w=600&q=80
Gallery1:  https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&q=80
Gallery2:  https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&q=80
```

---

## Task 1: Scaffold + CSS Foundation + Header

**Files:**
- Create: `drafts/cafe-u-yulii.html`

**Delivers:** File exists, Google Fonts loaded, CSS variables defined, sticky header with logo and nav working. Page opens in browser without errors.

- [ ] **Step 1: Create the file with HTML skeleton, fonts, CSS variables and reset**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Кафе «У Юлии» — Узбекская кухня</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --dark:   #3D1A0E;
      --cream:  #F5F0E8;
      --gold:   #C8A96E;
      --white:  #FFFFFF;
      --overlay: rgba(30, 10, 5, 0.65);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body { font-family: 'Inter', sans-serif; background: var(--cream); color: var(--dark); }
    h1, h2, h3 { font-family: 'Playfair Display', serif; }
    a { text-decoration: none; color: inherit; }
    img { display: block; width: 100%; object-fit: cover; }
    .btn {
      display: inline-block;
      padding: 12px 28px;
      border-radius: 4px;
      font-family: 'Inter', sans-serif;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      border: 2px solid transparent;
      transition: all 0.2s;
    }
    .btn-gold { background: var(--gold); color: var(--dark); }
    .btn-gold:hover { background: #b8944f; }
    .btn-outline { background: transparent; color: var(--white); border-color: var(--white); }
    .btn-outline:hover { background: var(--white); color: var(--dark); }
    .section-title {
      font-size: clamp(26px, 4vw, 40px);
      color: var(--dark);
      text-align: center;
      margin-bottom: 48px;
    }
    section { padding: 80px 20px; }
    .container { max-width: 1100px; margin: 0 auto; }

    /* HEADER */
    header {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      padding: 0 20px;
      transition: background 0.3s;
    }
    header.scrolled { background: var(--dark); box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
    .header-inner {
      max-width: 1100px; margin: 0 auto;
      display: flex; align-items: center; justify-content: space-between;
      height: 70px;
    }
    .logo { font-family: 'Playfair Display', serif; font-size: 22px; color: var(--white); font-weight: 700; }
    nav { display: flex; gap: 32px; }
    nav a { color: var(--white); font-size: 14px; font-weight: 500; opacity: 0.9; transition: opacity 0.2s; }
    nav a:hover { opacity: 1; color: var(--gold); }
    .header-cta { /* reuses .btn .btn-gold */ }
    .burger { display: none; flex-direction: column; gap: 5px; cursor: pointer; padding: 4px; }
    .burger span { display: block; width: 24px; height: 2px; background: var(--white); transition: all 0.3s; }
    .mobile-nav {
      display: none; flex-direction: column; gap: 0;
      background: var(--dark); padding: 12px 20px 20px;
      position: absolute; top: 70px; left: 0; right: 0;
    }
    .mobile-nav a { color: var(--white); padding: 12px 0; font-size: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .mobile-nav.open { display: flex; }

    @media (max-width: 768px) {
      nav, .header-cta { display: none; }
      .burger { display: flex; }
    }
  </style>
</head>
<body>

<header id="header">
  <div class="header-inner">
    <div class="logo">У Юлии</div>
    <nav>
      <a href="#menu">Меню</a>
      <a href="#promo">Акции</a>
      <a href="#delivery">Доставка</a>
      <a href="#contacts">Контакты</a>
    </nav>
    <button class="btn btn-gold header-cta" onclick="openModal('book')">Забронировать стол</button>
    <div class="burger" id="burger" onclick="toggleMobileNav()">
      <span></span><span></span><span></span>
    </div>
  </div>
  <div class="mobile-nav" id="mobileNav">
    <a href="#menu" onclick="toggleMobileNav()">Меню</a>
    <a href="#promo" onclick="toggleMobileNav()">Акции</a>
    <a href="#delivery" onclick="toggleMobileNav()">Доставка</a>
    <a href="#contacts" onclick="toggleMobileNav()">Контакты</a>
    <button class="btn btn-gold" style="margin-top:16px;width:100%" onclick="openModal('book');toggleMobileNav()">Забронировать стол</button>
  </div>
</header>

<!-- SECTIONS WILL GO HERE -->

<script>
  // Header scroll effect
  window.addEventListener('scroll', () => {
    document.getElementById('header').classList.toggle('scrolled', window.scrollY > 60);
  });
  // Mobile nav
  function toggleMobileNav() {
    document.getElementById('mobileNav').classList.toggle('open');
  }
  // Modal stub — will be implemented in Task 5
  function openModal(type) { console.log('modal:', type); }
</script>
</body>
</html>
```

- [ ] **Step 2: Open in browser and verify**

Open `drafts/cafe-u-yulii.html` in browser.
Expected: white/cream page, no errors in console, header visible at top.

- [ ] **Step 3: Commit**

```bash
git add drafts/cafe-u-yulii.html
git commit -m "[agent] feat: cafe-u-yulii — scaffold + header"
```

---

## Task 2: Hero Section

**Files:**
- Modify: `drafts/cafe-u-yulii.html` — add hero CSS inside `<style>`, add hero HTML before `<!-- SECTIONS WILL GO HERE -->`

**Delivers:** Full-screen hero with background image, dark overlay, headline, subheadline, 3 CTA buttons, halal badge.

- [ ] **Step 1: Add hero CSS inside `<style>` (before closing `</style>`)**

```css
/* HERO */
#hero {
  min-height: 100vh;
  background: url('https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1920&q=80') center/cover no-repeat;
  position: relative;
  display: flex; align-items: center; justify-content: center;
  text-align: center; padding: 0 20px;
}
#hero::before {
  content: ''; position: absolute; inset: 0;
  background: var(--overlay);
}
.hero-content { position: relative; z-index: 1; max-width: 700px; }
.hero-badge {
  display: inline-block;
  background: var(--gold); color: var(--dark);
  font-size: 13px; font-weight: 700; letter-spacing: 1px;
  padding: 4px 14px; border-radius: 20px; margin-bottom: 20px;
}
.hero-title {
  font-size: clamp(36px, 6vw, 64px);
  color: var(--white); line-height: 1.15; margin-bottom: 18px;
}
.hero-sub {
  font-size: 18px; color: rgba(255,255,255,0.85);
  margin-bottom: 40px; line-height: 1.6;
}
.hero-btns { display: flex; gap: 14px; flex-wrap: wrap; justify-content: center; }
```

- [ ] **Step 2: Add hero HTML after the `<header>` closing tag (replace `<!-- SECTIONS WILL GO HERE -->`)**

```html
<!-- HERO -->
<section id="hero">
  <div class="hero-content">
    <div class="hero-badge">🌙 Халяль · Узбекская кухня</div>
    <h1 class="hero-title">Уютное кафе<br>для вкусных встреч</h1>
    <p class="hero-sub">Узбекская кухня, тёплая атмосфера<br>и забота в каждой детали</p>
    <div class="hero-btns">
      <button class="btn btn-gold" onclick="openModal('book')">Забронировать стол</button>
      <a href="#menu" class="btn btn-outline">Посмотреть меню</a>
      <button class="btn btn-outline" onclick="openModal('delivery')">Заказать доставку</button>
    </div>
  </div>
</section>

<!-- SECTIONS WILL GO HERE -->
```

- [ ] **Step 3: Open in browser and verify**

Expected: full-screen restaurant photo with dark overlay, white text, three buttons visible. On mobile — buttons stack vertically.

- [ ] **Step 4: Commit**

```bash
git add drafts/cafe-u-yulii.html
git commit -m "[agent] feat: cafe-u-yulii — hero section"
```

---

## Task 3: «Почему выбирают» + Меню

**Files:**
- Modify: `drafts/cafe-u-yulii.html` — add CSS + two sections HTML before `<!-- SECTIONS WILL GO HERE -->`

**Delivers:** 5-icon trust section and 6-dish menu grid with Unsplash food photos and placeholder prices.

- [ ] **Step 1: Add CSS inside `<style>`**

```css
/* WHY US */
#why { background: var(--white); }
.why-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 24px; text-align: center;
}
.why-item svg { width: 48px; height: 48px; margin: 0 auto 12px; }
.why-item p { font-size: 13px; line-height: 1.5; color: #555; }

/* MENU */
#menu { background: var(--cream); }
.menu-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.menu-card { background: var(--white); border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
.menu-card img { height: 180px; }
.menu-card-body { padding: 16px; }
.menu-card-body h3 { font-size: 16px; margin-bottom: 6px; }
.menu-card-body .price { font-size: 20px; font-weight: 700; color: var(--gold); }
.menu-cta { text-align: center; margin-top: 40px; }

@media (max-width: 768px) {
  .why-grid { grid-template-columns: repeat(2, 1fr); }
  .why-grid .why-item:last-child { grid-column: span 2; }
  .menu-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .menu-grid { grid-template-columns: 1fr; }
}
```

- [ ] **Step 2: Add HTML before `<!-- SECTIONS WILL GO HERE -->`**

```html
<!-- WHY US -->
<section id="why">
  <div class="container">
    <h2 class="section-title">Почему выбирают нас</h2>
    <div class="why-grid">
      <div class="why-item">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="22" stroke="#C8A96E" stroke-width="2"/>
          <path d="M24 12c-4 0-8 4-8 10s3 9 8 9 8-3 8-9-4-10-8-10z" fill="#C8A96E" opacity=".3"/>
          <path d="M16 34c0-4 3.6-7 8-7s8 3 8 7" stroke="#C8A96E" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p>Узбекская кухня<br>из свежих продуктов</p>
      </div>
      <div class="why-item">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="22" stroke="#C8A96E" stroke-width="2"/>
          <ellipse cx="24" cy="26" rx="12" ry="6" fill="#C8A96E" opacity=".3"/>
          <path d="M14 22h20M12 26h24" stroke="#C8A96E" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p>Большие порции<br>и вкусные блюда</p>
      </div>
      <div class="why-item">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="22" stroke="#C8A96E" stroke-width="2"/>
          <path d="M17 30l4-8 3 5 3-3 4 6" stroke="#C8A96E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p>Доступные цены<br>и честные порции</p>
      </div>
      <div class="why-item">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="22" stroke="#C8A96E" stroke-width="2"/>
          <path d="M24 14v10l6 6" stroke="#C8A96E" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p>Уютная атмосфера<br>как дома</p>
      </div>
      <div class="why-item">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="22" stroke="#C8A96E" stroke-width="2"/>
          <path d="M24 16v8l5 5" stroke="#C8A96E" stroke-width="2.5" stroke-linecap="round"/>
          <circle cx="24" cy="24" r="8" stroke="#C8A96E" stroke-width="1.5" opacity=".4"/>
        </svg>
        <p>Быстрое<br>обслуживание</p>
      </div>
    </div>
  </div>
</section>

<!-- MENU -->
<section id="menu">
  <div class="container">
    <h2 class="section-title">Наше меню</h2>
    <div class="menu-grid">
      <div class="menu-card">
        <img src="https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&q=80" alt="Плов по-узбекски" loading="lazy">
        <div class="menu-card-body">
          <h3>Плов по-узбекски</h3>
          <div class="price">350 ₽</div>
        </div>
      </div>
      <div class="menu-card">
        <img src="https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?w=400&q=80" alt="Лагман домашний" loading="lazy">
        <div class="menu-card-body">
          <h3>Лагман домашний</h3>
          <div class="price">320 ₽</div>
        </div>
      </div>
      <div class="menu-card">
        <img src="https://images.unsplash.com/photo-1547592180-85f173990554?w=400&q=80" alt="Шурпа" loading="lazy">
        <div class="menu-card-body">
          <h3>Шурпа</h3>
          <div class="price">290 ₽</div>
        </div>
      </div>
      <div class="menu-card">
        <img src="https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&q=80" alt="Манты" loading="lazy">
        <div class="menu-card-body">
          <h3>Манты</h3>
          <div class="price">300 ₽</div>
        </div>
      </div>
      <div class="menu-card">
        <img src="https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&q=80" alt="Шашлык из баранины" loading="lazy">
        <div class="menu-card-body">
          <h3>Шашлык из баранины</h3>
          <div class="price">550 ₽</div>
        </div>
      </div>
      <div class="menu-card">
        <img src="https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&q=80" alt="Самса" loading="lazy">
        <div class="menu-card-body">
          <h3>Самса</h3>
          <div class="price">150 ₽</div>
        </div>
      </div>
    </div>
    <div class="menu-cta">
      <a href="#contacts" class="btn btn-gold">Заказать столик</a>
    </div>
  </div>
</section>

<!-- SECTIONS WILL GO HERE -->
```

- [ ] **Step 3: Open in browser and verify**

Expected: cream background section with 5 gold SVG icons, then menu grid 3×2 with food photos and gold prices. On 768px — menu becomes 2×3, icons 2×3.

- [ ] **Step 4: Commit**

```bash
git add drafts/cafe-u-yulii.html
git commit -m "[agent] feat: cafe-u-yulii — why-us + menu sections"
```

---

## Task 4: Акции + Банкеты + Отзывы

**Files:**
- Modify: `drafts/cafe-u-yulii.html`

**Delivers:** Two-column promo/banquet block and three review cards with real ratings badges.

- [ ] **Step 1: Add CSS inside `<style>`**

```css
/* PROMO */
#promo { background: var(--white); }
.promo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
.promo-col h3 { font-size: 24px; margin-bottom: 24px; color: var(--dark); }
.promo-item { display: flex; gap: 16px; margin-bottom: 24px; align-items: flex-start; }
.promo-img { width: 100px; height: 80px; border-radius: 6px; object-fit: cover; flex-shrink: 0; }
.promo-text h4 { font-size: 16px; margin-bottom: 4px; }
.promo-text .tag { display: inline-block; background: var(--gold); color: var(--dark); font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 12px; margin-bottom: 6px; }
.promo-text p { font-size: 13px; color: #666; line-height: 1.5; }
.banquet-list { list-style: none; margin-bottom: 24px; }
.banquet-list li { padding: 8px 0; border-bottom: 1px solid #eee; font-size: 15px; }
.banquet-list li::before { content: '✓ '; color: var(--gold); font-weight: 700; }

/* REVIEWS */
#reviews { background: var(--cream); }
.reviews-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 40px; }
.review-card { background: var(--white); border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.review-author { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.review-avatar { width: 44px; height: 44px; border-radius: 50%; background: var(--gold); display: flex; align-items: center; justify-content: center; font-weight: 700; color: var(--dark); font-size: 18px; flex-shrink: 0; }
.review-name { font-weight: 600; font-size: 15px; }
.review-date { font-size: 12px; color: #999; }
.stars { color: var(--gold); font-size: 16px; margin-bottom: 10px; }
.review-text { font-size: 14px; line-height: 1.6; color: #555; }
.ratings-badges { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
.rating-badge { background: var(--white); border-radius: 8px; padding: 16px 28px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.rating-badge .score { font-size: 28px; font-weight: 700; color: var(--dark); }
.rating-badge .source { font-size: 13px; color: #888; margin-top: 2px; }
.rating-badge .stars-sm { color: var(--gold); font-size: 13px; }

@media (max-width: 768px) {
  .promo-grid { grid-template-columns: 1fr; }
  .reviews-grid { grid-template-columns: 1fr; }
}
```

- [ ] **Step 2: Add HTML before `<!-- SECTIONS WILL GO HERE -->`**

```html
<!-- PROMO + BANQUET -->
<section id="promo">
  <div class="container">
    <h2 class="section-title">Акции и банкеты</h2>
    <div class="promo-grid">
      <div class="promo-col">
        <h3>Акции</h3>
        <div class="promo-item">
          <img class="promo-img" src="https://images.unsplash.com/photo-1547592180-85f173990554?w=200&q=80" alt="Бизнес-ланч">
          <div class="promo-text">
            <div class="tag">от 250 ₽</div>
            <h4>Бизнес-ланч</h4>
            <p>Сытные обеды по будням<br>с 12:00 до 16:00</p>
          </div>
        </div>
        <div class="promo-item">
          <div style="width:100px;height:80px;border-radius:6px;background:var(--gold);display:flex;align-items:center;justify-content:center;font-size:32px;flex-shrink:0">🎂</div>
          <div class="promo-text">
            <div class="tag">−10%</div>
            <h4>Скидка именинникам</h4>
            <p>Действует 3 дня до и после дня рождения</p>
          </div>
        </div>
      </div>
      <div class="promo-col">
        <h3>Банкеты и мероприятия</h3>
        <ul class="banquet-list">
          <li>Свадьбы</li>
          <li>Юбилеи</li>
          <li>Корпоративы</li>
          <li>Дни рождения</li>
          <li>Поминальные обеды</li>
        </ul>
        <p style="font-size:14px;color:#666;margin-bottom:20px">До 60 человек · Индивидуальное меню · Профессиональное обслуживание</p>
        <button class="btn btn-gold" onclick="openModal('banquet')">Рассчитать банкет</button>
      </div>
    </div>
  </div>
</section>

<!-- REVIEWS -->
<section id="reviews">
  <div class="container">
    <h2 class="section-title">Отзывы наших гостей</h2>
    <div class="reviews-grid">
      <div class="review-card">
        <div class="review-author">
          <div class="review-avatar">О</div>
          <div>
            <div class="review-name">Ольга</div>
            <div class="review-date">12.05.2024</div>
          </div>
        </div>
        <div class="stars">★★★★★</div>
        <p class="review-text">Очень уютное место, вкусная еда и приятный персонал. Приходим сюда с семьёй уже не первый раз!</p>
      </div>
      <div class="review-card">
        <div class="review-author">
          <div class="review-avatar">А</div>
          <div>
            <div class="review-name">Александр</div>
            <div class="review-date">28.04.2024</div>
          </div>
        </div>
        <div class="stars">★★★★★</div>
        <p class="review-text">Отличное место для обеда! Бизнес-ланч по доступной цене и большие порции. Рекомендую.</p>
      </div>
      <div class="review-card">
        <div class="review-author">
          <div class="review-avatar">М</div>
          <div>
            <div class="review-name">Мария</div>
            <div class="review-date">15.01.2024</div>
          </div>
        </div>
        <div class="stars">★★★★★</div>
        <p class="review-text">Праздновали юбилей в кафе «У Юлии». Всё было на высшем уровне! Спасибо за организацию.</p>
      </div>
    </div>
    <div class="ratings-badges">
      <div class="rating-badge">
        <div class="score">4.4</div>
        <div class="stars-sm">★★★★½</div>
        <div class="source">Яндекс</div>
      </div>
      <div class="rating-badge">
        <div class="score">4.3</div>
        <div class="stars-sm">★★★★</div>
        <div class="source">Google</div>
      </div>
      <div class="rating-badge">
        <div class="score">5.0</div>
        <div class="stars-sm">★★★★★</div>
        <div class="source">2GIS</div>
      </div>
    </div>
  </div>
</section>

<!-- SECTIONS WILL GO HERE -->
```

- [ ] **Step 3: Open in browser and verify**

Expected: two-column promo block, three review cards with gold initials avatars, three rating badges below. On mobile — all stacks to single column.

- [ ] **Step 4: Commit**

```bash
git add drafts/cafe-u-yulii.html
git commit -m "[agent] feat: cafe-u-yulii — promo + reviews sections"
```

---

## Task 5: Доставка + Контакты + Футер

**Files:**
- Modify: `drafts/cafe-u-yulii.html`

**Delivers:** Delivery two-column block, contacts with real phone/WhatsApp/Instagram, footer.

- [ ] **Step 1: Add CSS inside `<style>`**

```css
/* DELIVERY */
#delivery { background: var(--dark); color: var(--white); }
#delivery .section-title { color: var(--white); }
.delivery-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center; }
.delivery-img { border-radius: 10px; overflow: hidden; }
.delivery-img img { height: 300px; }
.delivery-points { list-style: none; margin: 24px 0 32px; }
.delivery-points li { display: flex; gap: 12px; margin-bottom: 16px; font-size: 15px; align-items: flex-start; line-height: 1.5; }
.delivery-points li::before { content: '✓'; color: var(--gold); font-weight: 700; flex-shrink: 0; margin-top: 1px; }

/* CONTACTS */
#contacts { background: var(--cream); }
.contacts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; }
.contact-item { display: flex; gap: 14px; margin-bottom: 20px; align-items: flex-start; }
.contact-icon { font-size: 22px; flex-shrink: 0; margin-top: 2px; }
.contact-text strong { display: block; font-size: 15px; margin-bottom: 2px; }
.contact-text span { font-size: 14px; color: #666; }
.contact-text a { color: var(--dark); text-decoration: underline; }
.social-links { display: flex; gap: 12px; margin-top: 24px; flex-wrap: wrap; }
.social-link {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 6px;
  font-size: 14px; font-weight: 600;
}
.social-wa { background: #25D366; color: white; }
.social-ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; }
.map-placeholder {
  width: 100%; height: 280px; border-radius: 10px;
  background: #ddd url('https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=600&q=60') center/cover;
  position: relative; display: flex; align-items: center; justify-content: center;
}
.map-placeholder::before { content: ''; position: absolute; inset: 0; background: rgba(0,0,0,0.35); border-radius: 10px; }
.map-placeholder a {
  position: relative; z-index: 1;
  background: white; color: var(--dark);
  padding: 10px 20px; border-radius: 6px; font-weight: 600; font-size: 14px;
}

/* FOOTER */
footer {
  background: var(--dark); color: rgba(255,255,255,0.6);
  padding: 24px 20px; text-align: center; font-size: 13px;
}
footer strong { color: var(--white); }

@media (max-width: 768px) {
  .delivery-grid { grid-template-columns: 1fr; }
  .contacts-grid { grid-template-columns: 1fr; }
}
```

- [ ] **Step 2: Replace `<!-- SECTIONS WILL GO HERE -->` with delivery, contacts and footer HTML**

```html
<!-- DELIVERY -->
<section id="delivery">
  <div class="container">
    <h2 class="section-title">Доставка</h2>
    <div class="delivery-grid">
      <div class="delivery-img">
        <img src="https://images.unsplash.com/photo-1526367790999-0150786686a2?w=600&q=80" alt="Доставка блюд" loading="lazy">
      </div>
      <div>
        <p style="font-size:18px;margin-bottom:8px">Доставляем вкусные блюда прямо к вам домой или в офис</p>
        <ul class="delivery-points">
          <li>Быстрая доставка от 40 минут</li>
          <li>Минимальный заказ от 500 ₽</li>
          <li>Зона доставки — в пределах города</li>
          <li>Упаковка сохраняет тепло блюд</li>
        </ul>
        <button class="btn btn-gold" onclick="openModal('delivery')">Заказать доставку</button>
      </div>
    </div>
  </div>
</section>

<!-- CONTACTS -->
<section id="contacts">
  <div class="container">
    <h2 class="section-title">Контакты</h2>
    <div class="contacts-grid">
      <div>
        <div class="contact-item">
          <div class="contact-icon">📍</div>
          <div class="contact-text">
            <strong>Адрес</strong>
            <span>М/О, Беседы, Деревня Мильково, вл1с2</span>
          </div>
        </div>
        <div class="contact-item">
          <div class="contact-icon">📞</div>
          <div class="contact-text">
            <strong>Телефон</strong>
            <span><a href="tel:+79252754527">+7 (925) 27-545-27</a></span>
          </div>
        </div>
        <div class="contact-item">
          <div class="contact-icon">🕐</div>
          <div class="contact-text">
            <strong>Режим работы</strong>
            <span>Ежедневно с 10:00 до 22:00</span>
          </div>
        </div>
        <div class="social-links">
          <a href="https://wa.me/79055537530" target="_blank" class="social-link social-wa">
            <span>💬</span> WhatsApp
          </a>
          <a href="https://www.instagram.com/chaihana.namangan" target="_blank" class="social-link social-ig">
            <span>📸</span> Instagram
          </a>
        </div>
      </div>
      <div>
        <div class="map-placeholder">
          <a href="https://yandex.ru/maps/org/u_yulii/1579651285" target="_blank">Открыть на карте →</a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <p><strong>Кафе «У Юлии»</strong> · Узбекская кухня · Халяль</p>
  <p style="margin-top:6px">© 2024 · М/О, Беседы, Деревня Мильково, вл1с2 · <a href="tel:+79252754527" style="color:inherit">+7 (925) 27-545-27</a></p>
</footer>
```

- [ ] **Step 3: Open in browser and verify**

Expected: dark delivery section, cream contacts section with two phones and social buttons, dark footer. Map placeholder shows city photo with «Открыть на карте» button.

- [ ] **Step 4: Commit**

```bash
git add drafts/cafe-u-yulii.html
git commit -m "[agent] feat: cafe-u-yulii — delivery + contacts + footer"
```

---

## Task 6: Модальная форма + финальный JS

**Files:**
- Modify: `drafts/cafe-u-yulii.html` — add modal CSS, modal HTML before `</body>`, replace `openModal` stub with full implementation

**Delivers:** Working modal popup — opens from all CTA buttons with contextual title, validates name+phone, shows success state, auto-closes after 3s. Burger menu fully functional.

- [ ] **Step 1: Add modal CSS inside `<style>`**

```css
/* MODAL */
.modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,0.6); align-items: center; justify-content: center;
  padding: 20px;
}
.modal-overlay.open { display: flex; }
.modal {
  background: var(--white); border-radius: 12px;
  padding: 40px 36px; max-width: 480px; width: 100%;
  position: relative; animation: modalIn 0.25s ease;
}
@keyframes modalIn {
  from { transform: translateY(-20px); opacity: 0; }
  to   { transform: translateY(0);     opacity: 1; }
}
.modal-close {
  position: absolute; top: 16px; right: 18px;
  font-size: 24px; cursor: pointer; color: #999; background: none; border: none;
  line-height: 1;
}
.modal-close:hover { color: var(--dark); }
.modal h2 { font-size: 24px; margin-bottom: 8px; }
.modal p.modal-sub { font-size: 14px; color: #777; margin-bottom: 28px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--dark); }
.form-group input,
.form-group textarea {
  width: 100%; padding: 12px 14px;
  border: 1.5px solid #ddd; border-radius: 6px;
  font-family: 'Inter', sans-serif; font-size: 15px;
  transition: border-color 0.2s; outline: none;
}
.form-group input:focus,
.form-group textarea:focus { border-color: var(--gold); }
.form-group input.error { border-color: #e53e3e; }
.form-group textarea { resize: vertical; min-height: 80px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.modal-submit {
  width: 100%; padding: 14px;
  background: var(--gold); color: var(--dark);
  border: none; border-radius: 6px;
  font-size: 16px; font-weight: 700; cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: background 0.2s;
}
.modal-submit:hover { background: #b8944f; }
.modal-submit:disabled { opacity: 0.7; cursor: not-allowed; }
.modal-success {
  display: none; text-align: center; padding: 20px 0;
}
.modal-success .success-icon { font-size: 56px; margin-bottom: 16px; }
.modal-success h3 { font-size: 22px; margin-bottom: 10px; color: var(--dark); }
.modal-success p { color: #555; font-size: 15px; line-height: 1.6; }
```

- [ ] **Step 2: Add modal HTML before `</body>`**

```html
<!-- MODAL -->
<div class="modal-overlay" id="modalOverlay" onclick="handleOverlayClick(event)">
  <div class="modal" id="modal">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div id="modalForm">
      <h2 id="modalTitle">Забронировать стол</h2>
      <p class="modal-sub">Мы свяжемся с вами в течение 15 минут</p>
      <form onsubmit="submitForm(event)">
        <div class="form-group">
          <label>Ваше имя *</label>
          <input type="text" id="fieldName" placeholder="Иван Иванов">
        </div>
        <div class="form-group">
          <label>Телефон *</label>
          <input type="tel" id="fieldPhone" placeholder="+7 (___) ___-__-__">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Дата</label>
            <input type="date" id="fieldDate">
          </div>
          <div class="form-group">
            <label>Время</label>
            <input type="time" id="fieldTime" min="10:00" max="22:00">
          </div>
        </div>
        <div class="form-group">
          <label>Комментарий</label>
          <textarea id="fieldComment" placeholder="Количество гостей, пожелания..."></textarea>
        </div>
        <button type="submit" class="modal-submit" id="submitBtn">Отправить заявку</button>
      </form>
    </div>
    <div class="modal-success" id="modalSuccess">
      <div class="success-icon">🤝</div>
      <h3>Спасибо!</h3>
      <p>Мы свяжемся с вами<br>в течение 15 минут в WhatsApp</p>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Replace the `openModal` stub in `<script>` with full modal JS**

Find this block in the existing `<script>`:
```js
// Modal stub — will be implemented in Task 5
function openModal(type) { console.log('modal:', type); }
```

Replace it with:
```js
const MODAL_TITLES = {
  book:     'Забронировать стол',
  delivery: 'Заказать доставку',
  banquet:  'Рассчитать банкет',
};

function openModal(type) {
  document.getElementById('modalTitle').textContent = MODAL_TITLES[type] || 'Оставить заявку';
  document.getElementById('modalForm').style.display = '';
  document.getElementById('modalSuccess').style.display = 'none';
  document.getElementById('submitBtn').disabled = false;
  document.getElementById('submitBtn').textContent = 'Отправить заявку';
  ['fieldName','fieldPhone'].forEach(id => document.getElementById(id).classList.remove('error'));
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function handleOverlayClick(e) {
  if (e.target === document.getElementById('modalOverlay')) closeModal();
}

function submitForm(e) {
  e.preventDefault();
  const name  = document.getElementById('fieldName');
  const phone = document.getElementById('fieldPhone');
  let valid = true;
  if (!name.value.trim()) { name.classList.add('error'); valid = false; } else { name.classList.remove('error'); }
  const digits = phone.value.replace(/\D/g,'');
  if (digits.length < 10) { phone.classList.add('error'); valid = false; } else { phone.classList.remove('error'); }
  if (!valid) return;

  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.textContent = 'Отправляем...';

  setTimeout(() => {
    document.getElementById('modalForm').style.display = 'none';
    document.getElementById('modalSuccess').style.display = 'block';
    setTimeout(closeModal, 3000);
  }, 800);
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
```

- [ ] **Step 4: Open in browser and verify the full flow**

Check each of these:
1. Click «Забронировать стол» in header → modal opens with title «Забронировать стол»
2. Click «Заказать доставку» → modal opens with title «Заказать доставку»
3. Click «Рассчитать банкет» → modal opens with title «Рассчитать банкет»
4. Submit empty form → name and phone inputs get red border, form doesn't submit
5. Submit with name only → phone gets red border
6. Submit with both filled → button says «Отправляем...», then success screen appears, modal closes after 3s
7. Press Escape → modal closes
8. Click outside modal → modal closes
9. On mobile (resize to 375px) → modal fills screen with padding, form usable

- [ ] **Step 5: Commit**

```bash
git add drafts/cafe-u-yulii.html
git commit -m "[agent] feat: cafe-u-yulii — modal form + full JS"
```

---

## Done

After Task 6, the prototype is complete at `drafts/cafe-u-yulii.html`.
Send the file to the client via Telegram using `[ФАЙЛ: C:\Users\Administrator\projects\my-first-project\drafts\cafe-u-yulii.html]` tag.
