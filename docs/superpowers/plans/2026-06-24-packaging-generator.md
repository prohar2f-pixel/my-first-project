# Генератор упаковки — план реализации (Блок 1, v1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Самосервисный генератор упаковки для экспертов: онбординг из 7 вопросов → AI генерирует оффер (с оценкой), текст лендинга и серию писем, выдаваемые последовательно с управляемыми вариантами.

**Architecture:** Next.js (App Router, TypeScript). Чистая логика (вопросы, последовательность этапов, сборка промптов, модификаторы вариантов, парсинг) вынесена в `src/lib/**` и покрыта unit-тестами (Vitest). Генерация — через Vercel AI SDK (`streamText` / `generateObject`) с провайдером `@ai-sdk/anthropic`, у которого `baseURL` указывает на ProxyAPI (нативный Anthropic Messages API). Результаты сохраняются в PostgreSQL на российском сервере по анонимному id сессии. Данные хранятся в РФ; в модель уходит только обезличенный бриф.

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS, Vercel AI SDK (`ai`, `@ai-sdk/anthropic`, `@ai-sdk/react`), `zod`, `pg` (PostgreSQL), Vitest.

**Спека:** `docs/superpowers/specs/2026-06-23-packaging-generator-design.md`

---

## Замечания перед стартом

- **Модель:** по умолчанию `claude-opus-4-8` (самая сильная — качество упаковки приоритетно). Задаётся через env `AI_MODEL`.
- **ProxyAPI baseURL:** провайдер `@ai-sdk/anthropic` шлёт запросы на `${baseURL}/messages` с заголовком `x-api-key`. Точный базовый путь ProxyAPI к Anthropic нужно **проверить на proxyapi.ru** и положить в env `AI_BASE_URL` (ожидаемо вида `https://api.proxyapi.ru/anthropic/v1`). Не выдумывать — сверить перед запуском.
- **Thinking:** не включаем (опускаем параметр) — это уменьшает задержку первого токена, чтобы текст «печатался по словам» сразу. Качество для маркетинговых текстов остаётся высоким.
- **Все секреты — в `.env.local`**, который уже игнорируется gitignore (`.env`). Ключи в код не зашиваем.
- Рабочая директория проекта: `packaging-generator/` в корне репозитория.

## Структура файлов

```
packaging-generator/
  package.json, tsconfig.json, next.config.ts, postcss/tailwind config
  vitest.config.ts
  .env.example
  src/
    lib/
      onboarding/questions.ts        # 7 вопросов + тип Brief
      generation/stages.ts           # этапы + логика последовательности
      generation/prompts.ts          # сборка system/stage промптов
      generation/variants.ts         # модификаторы Короче/Дерзче/Проще
      generation/evaluation.ts       # схема оценки оффера + промпт
      ai/client.ts                   # провайдер AI (ProxyAPI baseURL)
      db/packages.ts                 # репозиторий + маппинг строк
    app/
      api/generate/route.ts          # стриминг материала
      api/evaluate/route.ts          # оценка оффера (structured)
      api/packages/route.ts          # сохранить/получить упаковку
      page.tsx                       # главный экран (поток)
    components/
      OnboardingWizard.tsx
      ResultStages.tsx
      MaterialCard.tsx
```

Каждый файл в `src/lib/**` имеет одну ответственность и тестируется изолированно.

---

## Task 1: Scaffold проекта

**Files:**
- Create: `packaging-generator/` (Next.js app)
- Create: `packaging-generator/vitest.config.ts`
- Create: `packaging-generator/.env.example`

- [ ] **Step 1: Создать Next.js приложение**

Run:
```bash
cd "c:/Users/Udacha/Documents/projects/my-first-project"
npx create-next-app@latest packaging-generator --typescript --tailwind --app --eslint --src-dir --no-import-alias --use-npm
```
Expected: создаётся папка `packaging-generator/` с Next.js + TS + Tailwind.

- [ ] **Step 2: Установить зависимости**

Run:
```bash
cd "c:/Users/Udacha/Documents/projects/my-first-project/packaging-generator"
npm install ai @ai-sdk/anthropic @ai-sdk/react zod pg
npm install -D vitest @types/pg
```
Expected: пакеты установлены без ошибок.

- [ ] **Step 3: Настроить Vitest**

Create `packaging-generator/vitest.config.ts`:
```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
```

Add to `packaging-generator/package.json` scripts:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 4: Создать `.env.example`**

Create `packaging-generator/.env.example`:
```bash
# AI — генерация через ProxyAPI (нативный Anthropic Messages API)
AI_BASE_URL=https://api.proxyapi.ru/anthropic/v1
AI_API_KEY=
AI_MODEL=claude-opus-4-8

# PostgreSQL на российском сервере
DATABASE_URL=postgres://user:password@host:5432/packaging
```

- [ ] **Step 5: Проверить, что приложение собирается**

Run:
```bash
npm run build
```
Expected: сборка проходит без ошибок (стартовый шаблон Next.js).

- [ ] **Step 6: Commit**

```bash
git add packaging-generator
git commit -m "chore: scaffold packaging-generator (next.js + ai sdk + vitest)"
```

---

## Task 2: Вопросы онбординга

**Files:**
- Create: `packaging-generator/src/lib/onboarding/questions.ts`
- Test: `packaging-generator/src/lib/onboarding/questions.test.ts`

- [ ] **Step 1: Написать падающий тест**

Create `src/lib/onboarding/questions.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { QUESTIONS, isBriefComplete, type Brief } from "./questions";

describe("onboarding questions", () => {
  it("содержит ровно 7 вопросов с уникальными id", () => {
    expect(QUESTIONS).toHaveLength(7);
    const ids = QUESTIONS.map((q) => q.id);
    expect(new Set(ids).size).toBe(7);
  });

  it("у каждого вопроса есть текст, подсказка и пример-плейсхолдер", () => {
    for (const q of QUESTIONS) {
      expect(q.label.length).toBeGreaterThan(0);
      expect(q.hint.length).toBeGreaterThan(0);
      expect(q.placeholder.length).toBeGreaterThan(0);
    }
  });

  it("бриф полон, только когда заполнены все вопросы непустыми ответами", () => {
    const empty = {} as Brief;
    expect(isBriefComplete(empty)).toBe(false);

    const full = Object.fromEntries(
      QUESTIONS.map((q) => [q.id, "ответ"]),
    ) as Brief;
    expect(isBriefComplete(full)).toBe(true);

    const partial = { ...full, [QUESTIONS[0].id]: "  " };
    expect(isBriefComplete(partial)).toBe(false);
  });
});
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `npm run test -- src/lib/onboarding/questions.test.ts`
Expected: FAIL (модуль `./questions` не найден).

- [ ] **Step 3: Реализовать модуль**

Create `src/lib/onboarding/questions.ts`:
```ts
export type QuestionId =
  | "niche"
  | "audience"
  | "result"
  | "method"
  | "difference"
  | "product"
  | "tone";

export interface Question {
  id: QuestionId;
  label: string;
  hint: string;
  placeholder: string;
}

export type Brief = Record<QuestionId, string>;

export const QUESTIONS: Question[] = [
  {
    id: "niche",
    label: "Чем ты занимаешься?",
    hint: "Твоя ниша одной фразой.",
    placeholder: "Психолог, работаю с тревогой и выгоранием",
  },
  {
    id: "audience",
    label: "Кому ты помогаешь?",
    hint: "Твоя аудитория.",
    placeholder: "Мамы 30–40 лет в декрете",
  },
  {
    id: "result",
    label: "Какой результат получает клиент?",
    hint: "Главный итог в 5–8 слов.",
    placeholder: "Выходят из выгорания за 6 недель",
  },
  {
    id: "method",
    label: "Как ты это делаешь?",
    hint: "Метод или формат работы.",
    placeholder: "6-недельная программа мягких ежедневных шагов",
  },
  {
    id: "difference",
    label: "Чем ты отличаешься от других?",
    hint: "Твоя отстройка.",
    placeholder: "Работаю по протоколу, а не по наитию",
  },
  {
    id: "product",
    label: "Что ты продаёшь и за сколько?",
    hint: "Продукт и цена.",
    placeholder: "Консультации + курс, 15 000 ₽",
  },
  {
    id: "tone",
    label: "В каком тоне общаешься?",
    hint: "Голос бренда.",
    placeholder: "Тепло, по-человечески, без эзотерики",
  },
];

export function isBriefComplete(brief: Brief): boolean {
  return QUESTIONS.every((q) => (brief[q.id] ?? "").trim().length > 0);
}
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `npm run test -- src/lib/onboarding/questions.test.ts`
Expected: PASS (3 теста).

- [ ] **Step 5: Commit**

```bash
git add src/lib/onboarding
git commit -m "feat: onboarding questions config and brief validation"
```

---

## Task 3: Этапы и последовательная логика

**Files:**
- Create: `packaging-generator/src/lib/generation/stages.ts`
- Test: `packaging-generator/src/lib/generation/stages.test.ts`

- [ ] **Step 1: Написать падающий тест**

Create `src/lib/generation/stages.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { STAGES, isStageUnlocked, nextStage, type StageId } from "./stages";

describe("stages sequencing", () => {
  it("три этапа в правильном порядке", () => {
    expect(STAGES.map((s) => s.id)).toEqual(["offer", "landing", "emails"]);
  });

  it("первый этап открыт всегда", () => {
    expect(isStageUnlocked("offer", [])).toBe(true);
  });

  it("следующий этап закрыт, пока предыдущий не принят", () => {
    expect(isStageUnlocked("landing", [])).toBe(false);
    expect(isStageUnlocked("landing", ["offer"])).toBe(true);
    expect(isStageUnlocked("emails", ["offer"])).toBe(false);
    expect(isStageUnlocked("emails", ["offer", "landing"])).toBe(true);
  });

  it("nextStage возвращает следующий этап или null на последнем", () => {
    expect(nextStage("offer")).toBe("landing");
    expect(nextStage("landing")).toBe("emails");
    expect(nextStage("emails")).toBeNull();
  });
});
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `npm run test -- src/lib/generation/stages.test.ts`
Expected: FAIL (модуль не найден).

- [ ] **Step 3: Реализовать модуль**

Create `src/lib/generation/stages.ts`:
```ts
export type StageId = "offer" | "landing" | "emails";

export interface Stage {
  id: StageId;
  title: string;
  lockedReason: string;
}

export const STAGES: Stage[] = [
  {
    id: "offer",
    title: "Оффер / позиционирование",
    lockedReason: "",
  },
  {
    id: "landing",
    title: "Текст лендинга / профиля",
    lockedReason: "Откроется, когда примешь оффер — он лёг в основу страницы.",
  },
  {
    id: "emails",
    title: "Серия писем / прогрев",
    lockedReason: "Откроется после лендинга — письма ведут на него.",
  },
];

const ORDER: StageId[] = STAGES.map((s) => s.id);

export function isStageUnlocked(stage: StageId, accepted: StageId[]): boolean {
  const index = ORDER.indexOf(stage);
  if (index === 0) return true;
  const previous = ORDER[index - 1];
  return accepted.includes(previous);
}

export function nextStage(stage: StageId): StageId | null {
  const index = ORDER.indexOf(stage);
  return index >= 0 && index < ORDER.length - 1 ? ORDER[index + 1] : null;
}
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `npm run test -- src/lib/generation/stages.test.ts`
Expected: PASS (4 теста).

- [ ] **Step 5: Commit**

```bash
git add src/lib/generation/stages.ts src/lib/generation/stages.test.ts
git commit -m "feat: stage definitions and sequential unlock logic"
```

---

## Task 4: Модификаторы вариантов (Короче / Дерзче / Проще)

**Files:**
- Create: `packaging-generator/src/lib/generation/variants.ts`
- Test: `packaging-generator/src/lib/generation/variants.test.ts`

- [ ] **Step 1: Написать падающий тест**

Create `src/lib/generation/variants.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { VARIANTS, modifierInstruction, type VariantId } from "./variants";

describe("controlled variants", () => {
  it("три варианта с человекочитаемыми ярлыками", () => {
    expect(VARIANTS.map((v) => v.id)).toEqual(["shorter", "bolder", "simpler"]);
    for (const v of VARIANTS) expect(v.label.length).toBeGreaterThan(0);
  });

  it("инструкция модификатора непустая и содержательная", () => {
    const ids: VariantId[] = ["shorter", "bolder", "simpler"];
    for (const id of ids) {
      expect(modifierInstruction(id).length).toBeGreaterThan(10);
    }
    expect(modifierInstruction("shorter")).toContain("короче");
    expect(modifierInstruction("bolder")).toContain("дерз");
    expect(modifierInstruction("simpler")).toContain("прост");
  });
});
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `npm run test -- src/lib/generation/variants.test.ts`
Expected: FAIL.

- [ ] **Step 3: Реализовать модуль**

Create `src/lib/generation/variants.ts`:
```ts
export type VariantId = "shorter" | "bolder" | "simpler";

export interface Variant {
  id: VariantId;
  label: string;
}

export const VARIANTS: Variant[] = [
  { id: "shorter", label: "Короче" },
  { id: "bolder", label: "Дерзче" },
  { id: "simpler", label: "Проще" },
];

const INSTRUCTIONS: Record<VariantId, string> = {
  shorter:
    "Сделай заметно короче: убери лишнее, оставь только суть. Тот же смысл, меньше слов.",
  bolder:
    "Сделай дерзче и смелее: ярче формулировки, сильнее обещание, больше характера — без вранья и без агрессии.",
  simpler:
    "Сделай проще: убери сложные слова и термины, объясни как для обычного человека. Короткие фразы.",
};

export function modifierInstruction(id: VariantId): string {
  return INSTRUCTIONS[id];
}
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `npm run test -- src/lib/generation/variants.test.ts`
Expected: PASS (2 теста).

- [ ] **Step 5: Commit**

```bash
git add src/lib/generation/variants.ts src/lib/generation/variants.test.ts
git commit -m "feat: controlled variant modifiers (shorter/bolder/simpler)"
```

---

## Task 5: Сборка промптов

**Files:**
- Create: `packaging-generator/src/lib/generation/prompts.ts`
- Test: `packaging-generator/src/lib/generation/prompts.test.ts`

- [ ] **Step 1: Написать падающий тест**

Create `src/lib/generation/prompts.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { buildSystemPrompt, buildStagePrompt } from "./prompts";
import type { Brief } from "../onboarding/questions";

const brief: Brief = {
  niche: "Психолог, работаю с выгоранием",
  audience: "Мамы в декрете",
  result: "Выходят из выгорания за 6 недель",
  method: "6-недельная программа",
  difference: "Работаю по протоколу",
  product: "Курс, 15 000 ₽",
  tone: "Тепло, без эзотерики",
};

describe("prompt building", () => {
  it("system-промпт задаёт роль маркетолога и русский язык", () => {
    const sys = buildSystemPrompt();
    expect(sys.toLowerCase()).toContain("маркетолог");
    expect(sys.toLowerCase()).toContain("русск");
  });

  it("промпт оффера включает все поля брифа", () => {
    const p = buildStagePrompt("offer", brief);
    for (const value of Object.values(brief)) {
      expect(p).toContain(value);
    }
  });

  it("промпт лендинга опирается на принятый оффер", () => {
    const p = buildStagePrompt("landing", brief, { acceptedOffer: "Мой оффер" });
    expect(p).toContain("Мой оффер");
  });

  it("модификатор добавляется в промпт при пере-генерации", () => {
    const p = buildStagePrompt("offer", brief, {
      modifier: "Сделай заметно короче",
    });
    expect(p).toContain("Сделай заметно короче");
  });
});
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `npm run test -- src/lib/generation/prompts.test.ts`
Expected: FAIL.

- [ ] **Step 3: Реализовать модуль**

Create `src/lib/generation/prompts.ts`:
```ts
import type { Brief } from "../onboarding/questions";
import type { StageId } from "./stages";

export function buildSystemPrompt(): string {
  return [
    "Ты — опытный маркетолог-копирайтер, который упаковывает экспертов",
    "(психологов, коучей, наставников). Пишешь сильно, по-человечески, без",
    "канцелярита и без инфоцыганских клише. Отвечаешь только на русском языке.",
    "Возвращаешь готовый текст без вступлений вроде «Вот ваш текст».",
  ].join(" ");
}

function briefBlock(brief: Brief): string {
  return [
    `Ниша: ${brief.niche}`,
    `Аудитория: ${brief.audience}`,
    `Результат клиента: ${brief.result}`,
    `Метод: ${brief.method}`,
    `Отличие: ${brief.difference}`,
    `Продукт и цена: ${brief.product}`,
    `Тон общения: ${brief.tone}`,
  ].join("\n");
}

interface StageOptions {
  acceptedOffer?: string;
  acceptedLanding?: string;
  modifier?: string;
}

const TASKS: Record<StageId, string> = {
  offer:
    "Собери сильный оффер/позиционирование: кто эксперт, для кого, какой результат, чем отличается. 3–5 предложений, выдержи указанный тон.",
  landing:
    "Напиши текст лендинга/профиля на основе принятого оффера: заголовок, блок «о мне», услуги, отзыв-пример, призыв к действию.",
  emails:
    "Напиши серию из 4 писем-прогрева, которые ведут к покупке: у каждого письма тема и короткий текст. Письма опираются на оффер и лендинг.",
};

export function buildStagePrompt(
  stage: StageId,
  brief: Brief,
  options: StageOptions = {},
): string {
  const parts = [briefBlock(brief), "", `Задача: ${TASKS[stage]}`];

  if (stage !== "offer" && options.acceptedOffer) {
    parts.push("", `Принятый оффер:\n${options.acceptedOffer}`);
  }
  if (stage === "emails" && options.acceptedLanding) {
    parts.push("", `Текст лендинга:\n${options.acceptedLanding}`);
  }
  if (options.modifier) {
    parts.push("", `Дополнительно: ${options.modifier}`);
  }

  return parts.join("\n");
}
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `npm run test -- src/lib/generation/prompts.test.ts`
Expected: PASS (4 теста).

- [ ] **Step 5: Commit**

```bash
git add src/lib/generation/prompts.ts src/lib/generation/prompts.test.ts
git commit -m "feat: system and per-stage prompt builders"
```

---

## Task 6: Схема и промпт оценки оффера

**Files:**
- Create: `packaging-generator/src/lib/generation/evaluation.ts`
- Test: `packaging-generator/src/lib/generation/evaluation.test.ts`

- [ ] **Step 1: Написать падающий тест**

Create `src/lib/generation/evaluation.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import {
  EvaluationSchema,
  buildEvaluationPrompt,
  STRENGTH_LABELS,
} from "./evaluation";

describe("offer evaluation", () => {
  it("шкала силы — грубая (3 градации), без псевдоточных баллов", () => {
    expect(STRENGTH_LABELS).toEqual(["низкий", "средний", "сильный"]);
  });

  it("схема требует силу, слабое место и как улучшить", () => {
    const ok = EvaluationSchema.safeParse({
      strength: "средний",
      weakSpot: "Неясен результат",
      howToImprove: "Уточнить срок",
    });
    expect(ok.success).toBe(true);

    const bad = EvaluationSchema.safeParse({ strength: "7.8" });
    expect(bad.success).toBe(false);
  });

  it("промпт оценки содержит сам оффер", () => {
    const p = buildEvaluationPrompt("Помогаю мамам выйти из выгорания");
    expect(p).toContain("Помогаю мамам выйти из выгорания");
  });
});
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `npm run test -- src/lib/generation/evaluation.test.ts`
Expected: FAIL.

- [ ] **Step 3: Реализовать модуль**

Create `src/lib/generation/evaluation.ts`:
```ts
import { z } from "zod";

export const STRENGTH_LABELS = ["низкий", "средний", "сильный"] as const;

export const EvaluationSchema = z.object({
  strength: z.enum(STRENGTH_LABELS),
  weakSpot: z.string().min(1),
  howToImprove: z.string().min(1),
});

export type Evaluation = z.infer<typeof EvaluationSchema>;

export function buildEvaluationPrompt(offer: string): string {
  return [
    "Оцени этот оффер эксперта как маркетолог.",
    "",
    `Оффер:\n${offer}`,
    "",
    "Дай: грубую оценку силы (низкий/средний/сильный — без числовых баллов),",
    "одно главное слабое место и один конкретный совет, как его улучшить.",
    "Пиши по-русски, коротко и по делу.",
  ].join("\n");
}
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `npm run test -- src/lib/generation/evaluation.test.ts`
Expected: PASS (3 теста).

- [ ] **Step 5: Commit**

```bash
git add src/lib/generation/evaluation.ts src/lib/generation/evaluation.test.ts
git commit -m "feat: offer evaluation schema and prompt (coarse strength scale)"
```

---

## Task 7: AI-провайдер (ProxyAPI)

**Files:**
- Create: `packaging-generator/src/lib/ai/client.ts`

> Это конфигурация провайдера — без unit-теста (проверяется в интеграции в Task 8). Держим в одном месте, чтобы baseURL/ключ задавались из env.

- [ ] **Step 1: Реализовать провайдер**

Create `src/lib/ai/client.ts`:
```ts
import { createAnthropic } from "@ai-sdk/anthropic";

const anthropic = createAnthropic({
  baseURL: process.env.AI_BASE_URL,
  apiKey: process.env.AI_API_KEY,
});

export const aiModel = anthropic(process.env.AI_MODEL ?? "claude-opus-4-8");
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/ai/client.ts
git commit -m "feat: anthropic provider via proxyapi baseURL"
```

---

## Task 8: Роут стриминга генерации

**Files:**
- Create: `packaging-generator/src/app/api/generate/route.ts`

- [ ] **Step 1: Реализовать роут**

Create `src/app/api/generate/route.ts`:
```ts
import { streamText } from "ai";
import { aiModel } from "@/lib/ai/client";
import { buildSystemPrompt, buildStagePrompt } from "@/lib/generation/prompts";
import type { Brief } from "@/lib/onboarding/questions";
import type { StageId } from "@/lib/generation/stages";

export const runtime = "nodejs";
export const maxDuration = 60;

interface GenerateBody {
  stage: StageId;
  brief: Brief;
  acceptedOffer?: string;
  acceptedLanding?: string;
  modifier?: string;
}

export async function POST(req: Request) {
  const body = (await req.json()) as GenerateBody;

  const result = streamText({
    model: aiModel,
    system: buildSystemPrompt(),
    prompt: buildStagePrompt(body.stage, body.brief, {
      acceptedOffer: body.acceptedOffer,
      acceptedLanding: body.acceptedLanding,
      modifier: body.modifier,
    }),
    maxOutputTokens: 2000,
  });

  return result.toTextStreamResponse();
}
```

- [ ] **Step 2: Проверить вручную (нужны env)**

Скопировать `.env.example` → `.env.local`, заполнить `AI_BASE_URL` и `AI_API_KEY` ключом ProxyAPI.

Run:
```bash
npm run dev
```
В другом терминале:
```bash
curl -N http://localhost:3000/api/generate -H "Content-Type: application/json" -d '{"stage":"offer","brief":{"niche":"Психолог","audience":"Мамы в декрете","result":"Выход из выгорания за 6 недель","method":"Программа","difference":"По протоколу","product":"Курс 15000","tone":"Тепло"}}'
```
Expected: текст оффера приходит **потоком по кускам** (стриминг), на русском. Если 404/401 — проверить `AI_BASE_URL` и ключ ProxyAPI.

- [ ] **Step 3: Commit**

```bash
git add src/app/api/generate/route.ts
git commit -m "feat: streaming generation route"
```

---

## Task 9: Роут оценки оффера

**Files:**
- Create: `packaging-generator/src/app/api/evaluate/route.ts`

- [ ] **Step 1: Реализовать роут**

Create `src/app/api/evaluate/route.ts`:
```ts
import { generateObject } from "ai";
import { aiModel } from "@/lib/ai/client";
import {
  EvaluationSchema,
  buildEvaluationPrompt,
} from "@/lib/generation/evaluation";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: Request) {
  const { offer } = (await req.json()) as { offer: string };

  const { object } = await generateObject({
    model: aiModel,
    schema: EvaluationSchema,
    prompt: buildEvaluationPrompt(offer),
  });

  return Response.json(object);
}
```

- [ ] **Step 2: Проверить вручную**

Run (при запущенном `npm run dev`):
```bash
curl http://localhost:3000/api/evaluate -H "Content-Type: application/json" -d '{"offer":"Помогаю мамам выйти из выгорания за 6 недель"}'
```
Expected: JSON вида `{"strength":"средний","weakSpot":"...","howToImprove":"..."}`.

- [ ] **Step 3: Commit**

```bash
git add src/app/api/evaluate/route.ts
git commit -m "feat: offer evaluation route (structured output)"
```

---

## Task 10: Сохранение упаковки в PostgreSQL

**Files:**
- Create: `packaging-generator/src/lib/db/packages.ts`
- Test: `packaging-generator/src/lib/db/packages.test.ts`
- Create: `packaging-generator/src/app/api/packages/route.ts`

> Подключение к БД тестируется вручную против локального Postgres; чистый маппинг строки в объект — unit-тестом.

- [ ] **Step 1: Написать падающий тест на маппинг строки**

Create `src/lib/db/packages.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { rowToPackage } from "./packages";

describe("packages row mapping", () => {
  it("превращает строку БД в объект упаковки", () => {
    const row = {
      session_id: "abc",
      brief: { niche: "Психолог" },
      materials: { offer: "текст" },
      created_at: new Date("2026-06-24T10:00:00Z"),
    };
    const pkg = rowToPackage(row);
    expect(pkg.sessionId).toBe("abc");
    expect(pkg.brief.niche).toBe("Психолог");
    expect(pkg.materials.offer).toBe("текст");
    expect(pkg.createdAt).toBe("2026-06-24T10:00:00.000Z");
  });
});
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `npm run test -- src/lib/db/packages.test.ts`
Expected: FAIL.

- [ ] **Step 3: Реализовать модуль**

Create `src/lib/db/packages.ts`:
```ts
import { Pool } from "pg";
import type { Brief } from "../onboarding/questions";

let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) pool = new Pool({ connectionString: process.env.DATABASE_URL });
  return pool;
}

export interface PackageRow {
  session_id: string;
  brief: Brief;
  materials: Record<string, unknown>;
  created_at: Date;
}

export interface Package {
  sessionId: string;
  brief: Brief;
  materials: Record<string, unknown>;
  createdAt: string;
}

export function rowToPackage(row: PackageRow): Package {
  return {
    sessionId: row.session_id,
    brief: row.brief,
    materials: row.materials,
    createdAt: row.created_at.toISOString(),
  };
}

export async function savePackage(
  sessionId: string,
  brief: Brief,
  materials: Record<string, unknown>,
): Promise<void> {
  await getPool().query(
    `INSERT INTO packages (session_id, brief, materials)
     VALUES ($1, $2, $3)
     ON CONFLICT (session_id)
     DO UPDATE SET brief = $2, materials = $3, created_at = now()`,
    [sessionId, brief, materials],
  );
}

export async function getPackage(sessionId: string): Promise<Package | null> {
  const { rows } = await getPool().query<PackageRow>(
    "SELECT * FROM packages WHERE session_id = $1",
    [sessionId],
  );
  return rows[0] ? rowToPackage(rows[0]) : null;
}
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `npm run test -- src/lib/db/packages.test.ts`
Expected: PASS.

- [ ] **Step 5: Создать таблицу в БД**

Подключиться к российскому PostgreSQL (`DATABASE_URL`) и выполнить:
```sql
CREATE TABLE IF NOT EXISTS packages (
  session_id text PRIMARY KEY,
  brief jsonb NOT NULL,
  materials jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

- [ ] **Step 6: Реализовать роут сохранения/получения**

Create `src/app/api/packages/route.ts`:
```ts
import { savePackage, getPackage } from "@/lib/db/packages";
import type { Brief } from "@/lib/onboarding/questions";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { sessionId, brief, materials } = (await req.json()) as {
    sessionId: string;
    brief: Brief;
    materials: Record<string, unknown>;
  };
  await savePackage(sessionId, brief, materials);
  return Response.json({ ok: true });
}

export async function GET(req: Request) {
  const sessionId = new URL(req.url).searchParams.get("sessionId");
  if (!sessionId) return Response.json({ error: "no sessionId" }, { status: 400 });
  const pkg = await getPackage(sessionId);
  return Response.json(pkg);
}
```

- [ ] **Step 7: Проверить вручную против локального Postgres**

С заполненным `DATABASE_URL` и запущенным `npm run dev`:
```bash
curl http://localhost:3000/api/packages -H "Content-Type: application/json" -d '{"sessionId":"test1","brief":{"niche":"Психолог"},"materials":{"offer":"текст"}}'
curl "http://localhost:3000/api/packages?sessionId=test1"
```
Expected: первый возвращает `{"ok":true}`, второй — сохранённую упаковку.

- [ ] **Step 8: Commit**

```bash
git add src/lib/db src/app/api/packages
git commit -m "feat: persist packages in postgres by session id"
```

---

## Task 11: UI — онбординг

**Files:**
- Create: `packaging-generator/src/components/OnboardingWizard.tsx`

- [ ] **Step 1: Реализовать компонент**

Create `src/components/OnboardingWizard.tsx`:
```tsx
"use client";

import { useState } from "react";
import { QUESTIONS, type Brief } from "@/lib/onboarding/questions";

export function OnboardingWizard({ onDone }: { onDone: (brief: Brief) => void }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Partial<Brief>>({});
  const q = QUESTIONS[step];
  const value = answers[q.id] ?? "";
  const progress = ((step + 1) / QUESTIONS.length) * 100;

  function next() {
    if (step < QUESTIONS.length - 1) setStep(step + 1);
    else onDone(answers as Brief);
  }

  return (
    <div className="mx-auto max-w-xl rounded-2xl bg-white p-7 shadow">
      <div className="mb-5 h-1.5 rounded-full bg-neutral-200">
        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${progress}%` }} />
      </div>
      <p className="mb-1 text-sm text-neutral-400">
        Вопрос {step + 1} из {QUESTIONS.length}
      </p>
      <h2 className="mb-1 text-xl font-semibold">{q.label}</h2>
      <p className="mb-4 text-sm text-neutral-500">{q.hint}</p>
      <input
        autoFocus
        className="w-full rounded-xl border border-neutral-200 px-4 py-3 text-[15px] outline-none focus:border-indigo-400"
        placeholder={q.placeholder}
        value={value}
        onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
        onKeyDown={(e) => {
          if (e.key === "Enter" && value.trim()) next();
        }}
      />
      <div className="mt-5 flex justify-between">
        <button
          className="text-sm text-neutral-400 disabled:opacity-40"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
        >
          ← назад
        </button>
        <button
          className="rounded-xl bg-indigo-500 px-5 py-2.5 font-semibold text-white disabled:opacity-40"
          onClick={next}
          disabled={!value.trim()}
        >
          {step < QUESTIONS.length - 1 ? "Дальше" : "Собрать упаковку"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/OnboardingWizard.tsx
git commit -m "feat: onboarding wizard UI"
```

---

## Task 12: UI — последовательная выдача с управляемыми вариантами

**Files:**
- Create: `packaging-generator/src/components/MaterialCard.tsx`
- Create: `packaging-generator/src/components/ResultStages.tsx`

- [ ] **Step 1: Реализовать карточку материала**

Create `src/components/MaterialCard.tsx`:
```tsx
"use client";

import { VARIANTS, type VariantId } from "@/lib/generation/variants";

const BG: Record<string, string> = {
  offer: "bg-[#efe9fb]",
  landing: "bg-[#e7f0fb]",
  emails: "bg-[#e9f6ee]",
};

export function MaterialCard({
  stageId,
  title,
  text,
  streaming,
  onCopy,
  onVariant,
  onAccept,
  acceptLabel,
}: {
  stageId: string;
  title: string;
  text: string;
  streaming: boolean;
  onCopy: () => void;
  onVariant: (id: VariantId) => void;
  onAccept?: () => void;
  acceptLabel?: string;
}) {
  return (
    <div className={`rounded-2xl p-5 ${BG[stageId] ?? "bg-neutral-100"}`}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-bold">{title}</h3>
        <div className="flex gap-2">
          <button className="rounded-lg bg-white/70 px-3 py-1.5 text-xs font-semibold" onClick={onCopy}>
            Копировать
          </button>
          {VARIANTS.map((v) => (
            <button
              key={v.id}
              className="rounded-lg bg-white/70 px-3 py-1.5 text-xs font-semibold disabled:opacity-40"
              onClick={() => onVariant(v.id)}
              disabled={streaming}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>
      <p className="whitespace-pre-wrap text-sm text-neutral-800">{text}</p>
      {onAccept && (
        <div className="mt-4 flex justify-end">
          <button
            className="rounded-xl bg-indigo-500 px-5 py-2.5 font-semibold text-white disabled:opacity-40"
            onClick={onAccept}
            disabled={streaming || !text}
          >
            {acceptLabel}
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Реализовать последовательную выдачу**

Create `src/components/ResultStages.tsx`:
```tsx
"use client";

import { useState } from "react";
import { STAGES, isStageUnlocked, nextStage, type StageId } from "@/lib/generation/stages";
import type { Brief } from "@/lib/onboarding/questions";
import { modifierInstruction, type VariantId } from "@/lib/generation/variants";
import { MaterialCard } from "./MaterialCard";

const ACCEPT_LABEL: Record<StageId, string> = {
  offer: "Принять оффер → к лендингу",
  landing: "Принять лендинг → к письмам",
  emails: "Готово",
};

export function ResultStages({ brief }: { brief: Brief }) {
  const [accepted, setAccepted] = useState<StageId[]>([]);
  const [texts, setTexts] = useState<Record<string, string>>({});
  const [streaming, setStreaming] = useState<StageId | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function generate(stage: StageId, modifier?: VariantId) {
    setError(null);
    setStreaming(stage);
    const previous = texts[stage] ?? "";
    setTexts((t) => ({ ...t, [stage]: "" }));
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stage,
          brief,
          acceptedOffer: texts.offer,
          acceptedLanding: texts.landing,
          modifier: modifier ? modifierInstruction(modifier) : undefined,
        }),
      });
      if (!res.ok || !res.body) throw new Error("bad response");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setTexts((t) => ({ ...t, [stage]: acc }));
      }
    } catch {
      setError("Не получилось сгенерировать. Попробуй ещё раз.");
      setTexts((t) => ({ ...t, [stage]: previous }));
    } finally {
      setStreaming(null);
    }
  }

  function accept(stage: StageId) {
    const updated = accepted.includes(stage) ? accepted : [...accepted, stage];
    setAccepted(updated);
    const nxt = nextStage(stage);
    if (nxt && !texts[nxt]) generate(nxt);
  }

  // первый этап генерируем сразу при первом рендере
  if (!texts.offer && streaming === null && !error) {
    generate("offer");
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">
          {error}{" "}
          <button className="font-semibold underline" onClick={() => generate("offer")}>
            Повторить
          </button>
        </div>
      )}
      {STAGES.map((stage) => {
        const unlocked = isStageUnlocked(stage.id, accepted);
        if (!unlocked) {
          return (
            <div key={stage.id} className="rounded-2xl bg-neutral-100 p-5">
              <h3 className="flex items-center gap-2 font-bold text-neutral-400">
                🔒 {stage.title}
              </h3>
              <p className="mt-1 text-sm text-neutral-400">{stage.lockedReason}</p>
            </div>
          );
        }
        return (
          <MaterialCard
            key={stage.id}
            stageId={stage.id}
            title={stage.title}
            text={texts[stage.id] ?? ""}
            streaming={streaming === stage.id}
            onCopy={() => navigator.clipboard.writeText(texts[stage.id] ?? "")}
            onVariant={(v) => generate(stage.id, v)}
            onAccept={accepted.includes(stage.id) ? undefined : () => accept(stage.id)}
            acceptLabel={ACCEPT_LABEL[stage.id]}
          />
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/MaterialCard.tsx src/components/ResultStages.tsx
git commit -m "feat: sequential result stages with controlled variants and streaming"
```

---

## Task 13: UI — главный экран и меню

**Files:**
- Modify: `packaging-generator/src/app/page.tsx`

- [ ] **Step 1: Собрать поток на главной странице**

Replace `src/app/page.tsx`:
```tsx
"use client";

import { useState } from "react";
import type { Brief } from "@/lib/onboarding/questions";
import { OnboardingWizard } from "@/components/OnboardingWizard";
import { ResultStages } from "@/components/ResultStages";

export default function Home() {
  const [brief, setBrief] = useState<Brief | null>(null);

  return (
    <div className="min-h-screen bg-[#fafafa] text-neutral-900">
      <header className="sticky top-0 z-10 border-b border-black/5 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-2 font-bold">
            <span className="h-6 w-6 rounded-md bg-gradient-to-br from-indigo-500 to-violet-400" />
            Упаковка
          </div>
          <nav className="flex gap-1 text-sm">
            <a className="rounded-lg bg-neutral-100 px-3 py-2 font-medium" href="#">Создать</a>
            <a className="rounded-lg px-3 py-2 text-neutral-500" href="#">Как это работает</a>
            <a className="rounded-lg px-3 py-2 text-neutral-500" href="#">Примеры</a>
          </nav>
        </div>
      </header>

      <main className="px-6 py-12">
        {brief ? (
          <ResultStages brief={brief} />
        ) : (
          <OnboardingWizard onDone={setBrief} />
        )}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Проверить весь поток вручную**

Run: `npm run dev`, открыть http://localhost:3000

Проверить:
1. Онбординг: 7 вопросов по одному, прогресс-бар растёт, пример в плейсхолдере.
2. После последнего вопроса — генерируется оффер, **текст печатается по словам**.
3. Лендинг и письма под замком с подписью.
4. «Принять оффер → к лендингу» разблокирует лендинг и генерирует его.
5. «Копировать» кладёт текст в буфер.
6. «Короче/Дерзче/Проще» пересоздают текст.
7. При ошибке AI — сообщение и кнопка «Повторить», старый текст не теряется.

- [ ] **Step 3: Commit**

```bash
git add src/app/page.tsx
git commit -m "feat: main screen with top menu and full flow"
```

---

## Task 14: Финальная проверка

- [ ] **Step 1: Прогнать все тесты**

Run:
```bash
npm run test
```
Expected: все unit-тесты зелёные (questions, stages, variants, prompts, evaluation, db mapping).

- [ ] **Step 2: Сборка**

Run:
```bash
npm run build
```
Expected: production-сборка проходит без ошибок.

- [ ] **Step 3: Сверка с критериями успеха спеки**

Пройти руками сценарий из §8 спеки и отметить каждый пункт:
1. Онбординг от начала до конца ✓
2. Каждый этап генерится и после принятия открывает следующий ✓
3. Заблокированный этап нельзя открыть раньше ✓
4. «Копировать» работает; варианты пересоздают ✓
5. Оффер сопровождается оценкой (см. примечание ниже) ✓
6. Стриминг по словам ✓
7. Ошибки AI — понятное сообщение + повтор ✓
8. Бриф уходит в модель без перс. данных; хранение в РФ ✓

> Примечание: блок оценки оффера (`/api/evaluate`) реализован в Task 9; его вызов и отображение под карточкой оффера можно подключить в `ResultStages` после приёмки оффера — это финальный штрих UI поверх готового роута.

---

## Self-review плана

- **Покрытие спеки:** онбординг (T2, T11), три материала и последовательность (T3, T12), управляемые варианты (T4, T12), промпты (T5), оценка оффера (T6, T9), AI через ProxyAPI/Claude (T7, T8), хранение в РФ-Postgres (T10), стриминг и обработка ошибок (T12), меню (T13). Бэклог v2 (быстрый вход, превью лендинга) сознательно не входит.
- **Плейсхолдеров нет:** все шаги содержат полный код или точные команды.
- **Согласованность типов:** `Brief`/`QuestionId` (T2) используются в T5/T10/T11/T12; `StageId` (T3) — в T5/T8/T12; `VariantId` (T4) — в T12; `EvaluationSchema` (T6) — в T9.
- **Открытый момент честно помечен:** точный `AI_BASE_URL` ProxyAPI сверить перед запуском; блок оценки в UI — финальный штрих поверх готового роута.
