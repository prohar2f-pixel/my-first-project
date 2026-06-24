# Генератор упаковки

Самосервисный веб-сервис для экспертов (психологи, коучи, наставники). Эксперт проходит короткий онбординг, и AI собирает ему упаковку: **оффер**, **текст лендинга** и **серию писем** — последовательно, с возможностью пере-генерации в нужном тоне.

Это **Блок 1** более крупной цели «полная автоворонка». В первой версии нет входа и оплаты — цель проверить спрос.

Документы: дизайн-спека `../docs/superpowers/specs/2026-06-23-packaging-generator-design.md`, план `../docs/superpowers/plans/2026-06-24-packaging-generator.md`, исследование `../research-packaging-funnel.md`.

## Как это работает

1. **Онбординг** (`src/components/OnboardingWizard.tsx`) — 7 коротких вопросов по одному на экран, с примерами-плейсхолдерами. На выходе — `Brief`.
2. **Генерация** — три этапа выдаются **строго по порядку**: оффер → лендинг → письма. Пока текущий этап не «принят», следующий под замком (`src/components/ResultStages.tsx`, логика последовательности — `src/lib/generation/stages.ts`).
3. **Стриминг** — текст печатается по словам. Серверный роут `src/app/api/generate/route.ts` отдаёт `streamText(...).toTextStreamResponse()`, клиент читает поток обычным `fetch` + reader.
4. **Управляемые варианты** — у каждого готового материала кнопки **Копировать / Короче / Дерзче / Проще** (`src/lib/generation/variants.ts`), которые пере-генерируют текст с нужным сдвигом.
5. **Сохранение** — при приёмке этапа упаковка сохраняется по анонимному `sessionId` (best-effort) в PostgreSQL через `src/app/api/packages/route.ts` → `src/lib/db/packages.ts`.

## Стек

- **Next.js 16** (App Router) + **React 19** + **TypeScript**
- **Tailwind CSS 4**
- **Vercel AI SDK** (`ai` v6) с провайдером **`@ai-sdk/anthropic`** v3 — генерация моделью **`claude-opus-4-8`** через **ProxyAPI** (нативный Anthropic Messages API)
- **`zod`** — схема структурированной оценки оффера
- **`pg`** — PostgreSQL
- **Vitest** — unit-тесты чистой логики

## Структура

```
src/
  lib/
    onboarding/questions.ts     # 7 вопросов, тип Brief, isBriefComplete
    generation/stages.ts        # STAGES, isStageUnlocked, nextStage
    generation/variants.ts      # VARIANTS, modifierInstruction (Короче/Дерзче/Проще)
    generation/prompts.ts       # buildSystemPrompt, buildStagePrompt
    generation/evaluation.ts    # EvaluationSchema (zod), buildEvaluationPrompt
    ai/client.ts                # aiModel — провайдер Anthropic с baseURL на ProxyAPI
    db/packages.ts              # savePackage, getPackage, rowToPackage
  app/
    api/generate/route.ts       # POST — стриминг материала
    api/evaluate/route.ts       # POST — структурированная оценка оффера
    api/packages/route.ts       # POST сохранить / GET получить упаковку
    page.tsx                    # главный экран + верхнее меню
  components/
    OnboardingWizard.tsx
    ResultStages.tsx
    MaterialCard.tsx
```

Чистая логика в `src/lib/**` покрыта unit-тестами (файлы `*.test.ts` рядом с модулями) — 6 файлов, запускаются через Vitest.

## Команды

```bash
npm run dev         # дев-сервер на http://localhost:3000
npm run build       # production-сборка
npm run start       # запуск собранного
npm run test        # unit-тесты (vitest run)
npm run test:watch  # тесты в watch-режиме
npm run lint        # eslint
```

## Переменные окружения

Скопируй `.env.example` в `.env.local` и заполни:

```bash
AI_BASE_URL=   # базовый путь ProxyAPI к Anthropic Messages API (сверить на proxyapi.ru)
AI_API_KEY=    # ключ ProxyAPI
AI_MODEL=claude-opus-4-8
DATABASE_URL=  # PostgreSQL на российском сервере
```

В модель уходит только обезличенный маркетинговый бриф (без персональных данных). Данные хранятся в PostgreSQL.

## База данных

Перед запуском создать таблицу в PostgreSQL:

```sql
CREATE TABLE IF NOT EXISTS packages (
  session_id TEXT PRIMARY KEY,
  brief      JSONB NOT NULL,
  materials  JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Что ещё не сделано

- Роут оценки оффера `/api/evaluate` реализован, но **пока не подключён к UI** (показ «слабое место / как улучшить» под карточкой оффера — следующий шаг).
- Валидации тел запросов в роутах (zod `safeParse`) нет — отложено как пост-MVP.
- Живые проверки (стриминг, оценка, сохранение) требуют ключа ProxyAPI и БД и в коде не выполнялись.
- v2-бэклог: быстрый вход (1 поле → черновик) и живой превью лендинга.

> Next.js здесь версии 16 — API и конвенции могут отличаться от привычных; см. `AGENTS.md`.
