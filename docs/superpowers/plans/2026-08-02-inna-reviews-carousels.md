# Inna Reviews Carousels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить две независимые адаптивные карусели для текстовых и аудиоотзывов с фото-заглушками и быстрым наполнением через CMS.

**Architecture:** `content.json` хранит два массива отзывов, `index.html` рендерит оба типа карточек и подключает общий контроллер scroll-snap карусели, а `admin/config.yml` предоставляет поля загрузки фото и аудио. Нативный `<audio>` создаётся только при наличии файла.

**Tech Stack:** HTML5, CSS Grid/Flexbox/scroll-snap, vanilla JavaScript, native Audio, Decap CMS, Node test runner.

## Global Constraints

- Не подключать сторонние библиотеки.
- Сохранить палитру и типографику Ladanie.
- Три текстовые карточки на десктопе, две на планшете, одна на телефоне.
- Пустое фото показывает инициалы; пустое аудио не показывает кнопку Play.
- Старый имитационный аудиоблок удалить.

---

### Task 1: Контракт данных отзывов

**Files:**
- Modify: `inna-therapy/tests/reviews-carousel.test.mjs`
- Modify: `inna-therapy/content.json`
- Modify: `inna-therapy/admin/config.yml`

**Interfaces:**
- Consumes: существующие `reviews[]`.
- Produces: `reviews[{text,author,role,photo}]` и `audio_reviews[{author,role,photo,audio,duration}]`.

- [ ] Написать падающий тест схемы двух массивов и пустых медиа-заглушек.
- [ ] Запустить `node --test inna-therapy/tests/reviews-carousel.test.mjs` и подтвердить падение из-за отсутствия полей.
- [ ] Добавить поля в JSON и Decap CMS; три аудиозаглушки хранить с пустым `audio`.
- [ ] Повторно запустить тест и получить PASS.

### Task 2: Две карусели и состояния карточек

**Files:**
- Modify: `inna-therapy/tests/reviews-carousel.test.mjs`
- Modify: `inna-therapy/index.html`

**Interfaces:**
- Consumes: оба массива из Task 1.
- Produces: `#text-reviews-carousel`, `#audio-reviews-carousel`, `renderTextReviews`, `renderAudioReviews`, `initReviewCarousel`.

- [ ] Написать падающие проверки двух независимых контейнеров, кнопок навигации, точек, аватаров-заглушек и настоящего `<audio>` только при непустом URL.
- [ ] Запустить тест и подтвердить падение на старой разметке.
- [ ] Заменить старый reviews-grid и имитационный voice-блок двумя scroll-snap каруселями.
- [ ] Реализовать общий контроллер: стрелки прокручивают одну страницу карточек, точки отражают текущую позицию, клавиши ArrowLeft/ArrowRight работают при фокусе.
- [ ] Запустить тест и получить PASS.

### Task 3: Адаптивный frontend-design и доступность

**Files:**
- Modify: `inna-therapy/tests/reviews-carousel.test.mjs`
- Modify: `inna-therapy/index.html`

**Interfaces:**
- Consumes: классы `.reviews-carousel`, `.review-slide`, `.review-avatar`, `.carousel-controls`.
- Produces: 3/2/1 адаптивную сетку и portrait-ribbon оформление.

- [ ] Добавить падающие проверки CSS scroll-snap, `prefers-reduced-motion`, focus-visible и брейкпоинтов.
- [ ] Реализовать токены, круглые фото, розовую навигационную линию, адаптивные размеры и заметный keyboard focus.
- [ ] Запустить все тесты: `node --test inna-therapy/tests/*.test.mjs`.
- [ ] Проверить JSON: `python3 -m json.tool inna-therapy/content.json`.
- [ ] Проверить diff: `git diff --check`.

### Task 4: Публикация

**Files:**
- Modify: только файлы задач 1–3 и эти документы.

**Interfaces:**
- Consumes: проверенный локальный diff.
- Produces: Vercel production с двумя каруселями.

- [ ] Синхронизировать `main` без перезаписи параллельных изменений.
- [ ] Зафиксировать только файлы раздела отзывов и документацию.
- [ ] Отправить `main` в GitHub.
- [ ] Проверить HTTP 200, две карусели, заглушки и отсутствие старого `.voice-reviews` на Vercel.
