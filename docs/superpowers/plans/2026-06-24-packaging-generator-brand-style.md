# Единый фирменный стиль для генератора упаковки — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перевести `packaging-generator/` на фирменный стиль aiprohar.ru (тёмная тема, фиолетовый акцент, Oswald, свечение кнопок, WebGL-дым), не меняя логику.

**Architecture:** Единый файл дизайн-токенов (`brand-tokens.css`) — источник стиля; `globals.css` пробрасывает токены в Tailwind v4 `@theme` и содержит слой компонентов (кнопки, эффекты). Фоновый эффект — тот же `fluid.js`, что на сайте, через клиентский компонент. Перекрашиваются 4 экранных файла; вся логика и тесты не трогаются.

**Tech Stack:** Next.js 16, React 19, Tailwind CSS v4 (CSS-first `@theme`), `next/font/google` (Oswald), WebGL (`fluid.js`, MIT).

**Примечание про TDD:** работа презентационная (CSS/разметка) — юнит-тестов на визуал нет. Каждая задача проверяется командой `npm run lint` (типы/линт) и коммитится; финальная задача прогоняет существующие 17 тестов, сборку и живую визуальную проверку. Команды запускать из папки `packaging-generator/`.

**Спецификация:** `docs/superpowers/specs/2026-06-24-packaging-generator-brand-style-design.md`

---

### Task 1: Файл дизайн-токенов `brand-tokens.css`

**Files:**
- Create: `packaging-generator/src/app/brand-tokens.css`

- [ ] **Step 1: Создать файл с токенами**

```css
/* ── Дизайн-токены бренда — источник стиля (из aiprohar.ru) ── */
:root {
  --p: #a855f7;
  --pd: #7c3aed;
  --pb: #c084fc;
  --bg: #0a0a0a;
  --bg2: #0d0d14;
  --card: rgba(255, 255, 255, 0.03);
  --card-solid: rgba(6, 6, 16, 0.95);
  --border: rgba(255, 255, 255, 0.07);
  --border-p: rgba(168, 85, 247, 0.35);
  --text: #e8e8e8;
  --muted: #808080;
  --p-gradient: linear-gradient(135deg, var(--p), var(--pd));
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif;
}
```

- [ ] **Step 2: Коммит**

```bash
git add packaging-generator/src/app/brand-tokens.css
git commit -m "feat(style): дизайн-токены бренда (brand-tokens.css)"
```

---

### Task 2: Переписать `globals.css` (тема + body + компоненты + эффекты)

**Files:**
- Modify: `packaging-generator/src/app/globals.css` (заменить целиком)

- [ ] **Step 1: Заменить содержимое `globals.css` целиком**

```css
@import "tailwindcss";
@import "./brand-tokens.css";

@theme inline {
  --color-bg: var(--bg);
  --color-bg2: var(--bg2);
  --color-card: var(--card);
  --color-card-solid: var(--card-solid);
  --color-border: var(--border);
  --color-border-p: var(--border-p);
  --color-text: var(--text);
  --color-muted: var(--muted);
  --color-accent: var(--p);
  --color-accent-d: var(--pd);
  --color-accent-b: var(--pb);
  --font-sans: var(--font-body);
  --font-display: var(--font-oswald);
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  line-height: 1.6;
  overflow-x: hidden;
}

/* зерно поверх фона */
body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: 0.4;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E");
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(168, 85, 247, 0.3); border-radius: 3px; }

*:focus-visible { outline: 2px solid var(--p); outline-offset: 3px; border-radius: 3px; }

/* ── Кнопки (порт из site.css) ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 13px 28px;
  border-radius: 12px;
  font-size: 0.93rem;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  transition: transform 0.25s, box-shadow 0.3s, background 0.25s, border-color 0.25s;
}
.btn::before {
  content: "";
  position: absolute;
  inset: -18px;
  border-radius: 22px;
  background: radial-gradient(ellipse at center, rgba(168, 85, 247, 0.55) 0%, rgba(109, 40, 217, 0.2) 45%, transparent 68%);
  filter: blur(20px);
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.4s, transform 0.5s;
  z-index: -1;
  pointer-events: none;
}
.btn::after {
  content: "";
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: calc(100% - 10px);
  height: 55px;
  background: radial-gradient(ellipse at 50% 100%, rgba(168, 85, 247, 0.6) 0%, rgba(139, 92, 246, 0.2) 40%, transparent 68%);
  filter: blur(16px);
  opacity: 0;
  transform: translateY(18px) scaleX(0.6);
  transition: opacity 0.35s, transform 0.5s;
  z-index: -1;
  pointer-events: none;
}
.btn:hover { transform: translateY(-3px); }
.btn:hover::before { opacity: 1; transform: scale(1.15); animation: sglow 2.2s ease-in-out infinite; }
.btn:hover::after { opacity: 1; transform: translateY(0) scaleX(1.1); animation: srise 1.8s ease-out infinite; }
.btn:disabled { opacity: 0.4; cursor: default; transform: none; }
.btn:disabled::before, .btn:disabled::after { opacity: 0; }

.btn-primary { background: var(--p); color: #fff; box-shadow: 0 0 22px rgba(168, 85, 247, 0.42), 0 4px 16px rgba(0, 0, 0, 0.3); }
.btn-primary:hover { background: #9333ea; box-shadow: 0 0 44px rgba(168, 85, 247, 0.75), 0 8px 28px rgba(0, 0, 0, 0.4); }

.btn-outline { background: rgba(255, 255, 255, 0.04); color: var(--text); border: 1px solid var(--border-p); }
.btn-outline:hover { border-color: rgba(168, 85, 247, 0.75); background: rgba(168, 85, 247, 0.07); }

/* малые кнопки (копировать/варианты) */
.btn-mini {
  display: inline-flex;
  align-items: center;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-p);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.btn-mini:hover { background: rgba(168, 85, 247, 0.1); border-color: rgba(168, 85, 247, 0.6); }
.btn-mini:disabled { opacity: 0.4; cursor: default; }

@keyframes sglow { 0%, 100% { transform: scale(1.1); opacity: 0.8; } 50% { transform: scale(1.28); opacity: 1; } }
@keyframes srise { 0% { opacity: 0.65; transform: translateY(0) scaleX(1.1) scaleY(0.7); } 100% { opacity: 0; transform: translateY(-45px) scaleX(1.7) scaleY(2); } }

/* плавное появление карточек */
.fi { animation: fadeUp 0.6s ease both; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }

/* мигающая каретка при стриминге */
.caret { display: inline-block; width: 2px; height: 1em; margin-left: 3px; background: var(--p); vertical-align: -2px; animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }

@media (prefers-reduced-motion: reduce) {
  .fi { animation: none; }
  .caret { animation: none; }
  .btn:hover::before, .btn:hover::after { animation: none; }
}
```

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок (CSS не линтуется eslint'ом, проверяем что проект собирается без TS-ошибок от прочих файлов).

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/app/globals.css
git commit -m "feat(style): тёмная тема, токены в @theme, кнопки и эффекты в globals.css"
```

---

### Task 3: Шрифт Oswald + favicon + metadata в `layout.tsx`

**Files:**
- Modify: `packaging-generator/src/app/layout.tsx` (заменить целиком)

- [ ] **Step 1: Заменить содержимое `layout.tsx` целиком**

```tsx
import type { Metadata } from "next";
import { Oswald } from "next/font/google";
import "./globals.css";

const oswald = Oswald({
  variable: "--font-oswald",
  weight: ["500", "600", "700"],
  subsets: ["latin", "cyrillic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Упаковка — генератор от АП",
  description:
    "Самосервисный генератор упаковки для экспертов: оффер, лендинг и серия писем за пару минут.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${oswald.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок. Если сборка ругается, что подмножество `cyrillic` недоступно для Oswald — убрать `"cyrillic"` из `subsets` (глифы кириллицы всё равно входят в файл шрифта).

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/app/layout.tsx
git commit -m "feat(style): шрифт Oswald, favicon и брендовые metadata"
```

---

### Task 4: Скопировать статические ассеты в `public/`

**Files:**
- Create: `packaging-generator/public/fluid.js` (копия `assets/fluid.js`)
- Create: `packaging-generator/public/logo.png` (копия `assets/logo.png`)
- Create: `packaging-generator/public/favicon.svg` (копия `assets/favicon.svg`)

- [ ] **Step 1: Скопировать файлы из корня репозитория**

Run (из корня репозитория `my-first-project/`):
```bash
mkdir -p packaging-generator/public
cp assets/fluid.js packaging-generator/public/fluid.js
cp assets/logo.png packaging-generator/public/logo.png
cp assets/favicon.svg packaging-generator/public/favicon.svg
```

- [ ] **Step 2: Проверить, что файлы на месте**

Run: `ls -1 packaging-generator/public/`
Expected: в списке есть `fluid.js`, `logo.png`, `favicon.svg`.

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/public/fluid.js packaging-generator/public/logo.png packaging-generator/public/favicon.svg
git commit -m "feat(style): брендовые ассеты (fluid.js, логотип, favicon) в public"
```

---

### Task 5: Компонент фонового эффекта `FluidBackground.tsx`

**Files:**
- Create: `packaging-generator/src/components/FluidBackground.tsx`

- [ ] **Step 1: Создать компонент**

```tsx
"use client";

import { useEffect } from "react";

// Подключает тот же WebGL-эффект, что на aiprohar.ru (public/fluid.js).
// Не запускается при prefers-reduced-motion. Глобальный флаг страхует
// от двойного запуска в React StrictMode (dev).
export function FluidBackground() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if ((window as unknown as { __fluidLoaded?: boolean }).__fluidLoaded) return;
    (window as unknown as { __fluidLoaded?: boolean }).__fluidLoaded = true;

    const script = document.createElement("script");
    script.src = "/fluid.js";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  return (
    <canvas
      id="smokeCanvas"
      className="pointer-events-none fixed inset-0 z-0"
      style={{ mixBlendMode: "screen" }}
    />
  );
}
```

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок.

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/components/FluidBackground.tsx
git commit -m "feat(style): компонент FluidBackground (WebGL-дым за курсором)"
```

---

### Task 6: Перекрасить `page.tsx` (шапка, логотип, фон, монтаж эффекта)

**Files:**
- Modify: `packaging-generator/src/app/page.tsx` (заменить целиком)

- [ ] **Step 1: Заменить содержимое `page.tsx` целиком**

```tsx
"use client";

import { useState } from "react";
import type { Brief } from "@/lib/onboarding/questions";
import { OnboardingWizard } from "@/components/OnboardingWizard";
import { ResultStages } from "@/components/ResultStages";
import { FluidBackground } from "@/components/FluidBackground";

export default function Home() {
  const [brief, setBrief] = useState<Brief | null>(null);

  return (
    <div className="relative min-h-screen text-text">
      <FluidBackground />

      <header className="sticky top-0 z-20 border-b border-white/5 bg-bg/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <a href="#" className="flex items-center">
            <img src="/logo.png" alt="АП" className="h-9 w-auto" />
          </a>
          <nav className="flex gap-1 text-sm">
            <a className="rounded-lg border border-border-p bg-accent/15 px-3 py-2 font-semibold text-white" href="#">
              Создать
            </a>
            <a className="rounded-lg px-3 py-2 text-muted transition-colors hover:text-text" href="#">
              Как это работает
            </a>
            <a className="rounded-lg px-3 py-2 text-muted transition-colors hover:text-text" href="#">
              Примеры
            </a>
          </nav>
        </div>
      </header>

      <main className="relative z-10 px-6 py-12">
        {brief ? <ResultStages brief={brief} /> : <OnboardingWizard onDone={setBrief} />}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок.

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/app/page.tsx
git commit -m "feat(style): тёмная шапка с логотипом и фон-эффект на главной"
```

---

### Task 7: Перекрасить `OnboardingWizard.tsx`

**Files:**
- Modify: `packaging-generator/src/components/OnboardingWizard.tsx` (заменить разметку в `return`)

- [ ] **Step 1: Заменить блок `return (...)` целиком**

Заменить весь `return (...)` (строки 18–54) на:

```tsx
  return (
    <div className="fi mx-auto max-w-xl rounded-[20px] border border-border bg-card-solid p-7 shadow-[0_22px_60px_rgba(0,0,0,0.45)]">
      <div className="mb-5 h-1.5 rounded-full bg-white/10">
        <div className="h-full rounded-full bg-accent" style={{ width: `${progress}%` }} />
      </div>
      <p className="mb-1 text-sm text-muted">
        Вопрос {step + 1} из {QUESTIONS.length}
      </p>
      <h2 className="mb-1 font-display text-2xl font-bold text-white">{q.label}</h2>
      <p className="mb-4 text-sm text-muted">{q.hint}</p>
      <input
        autoFocus
        className="w-full rounded-xl border border-border bg-white/[0.03] px-4 py-3 text-[15px] text-text outline-none transition-colors focus:border-border-p"
        placeholder={q.placeholder}
        value={value}
        onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
        onKeyDown={(e) => {
          if (e.key === "Enter" && value.trim()) next();
        }}
      />
      <div className="mt-5 flex items-center justify-between">
        <button
          className="text-sm text-muted transition-colors hover:text-text disabled:opacity-40"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
        >
          ← назад
        </button>
        <button className="btn btn-primary" onClick={next} disabled={!value.trim()}>
          {step < QUESTIONS.length - 1 ? "Дальше" : "Собрать упаковку"}
        </button>
      </div>
    </div>
  );
```

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок.

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/components/OnboardingWizard.tsx
git commit -m "feat(style): тёмный стиль мастера онбординга"
```

---

### Task 8: Перекрасить `MaterialCard.tsx` (+ мигающая каретка)

**Files:**
- Modify: `packaging-generator/src/components/MaterialCard.tsx` (заменить целиком)

- [ ] **Step 1: Заменить содержимое `MaterialCard.tsx` целиком**

```tsx
"use client";

import { VARIANTS, type VariantId } from "@/lib/generation/variants";

export function MaterialCard({
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
    <div className="fi overflow-hidden rounded-[20px] border border-border bg-card-solid p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-display text-lg font-bold text-white">{title}</h3>
        <div className="flex flex-wrap gap-2">
          <button className="btn-mini" onClick={onCopy}>
            Копировать
          </button>
          {VARIANTS.map((v) => (
            <button
              key={v.id}
              className="btn-mini"
              onClick={() => onVariant(v.id)}
              disabled={streaming}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>
      <p className="whitespace-pre-wrap text-sm text-text/90">
        {text}
        {streaming && <span className="caret" />}
      </p>
      {onAccept && (
        <div className="mt-4 flex justify-end">
          <button className="btn btn-primary" onClick={onAccept} disabled={streaming || !text}>
            {acceptLabel}
          </button>
        </div>
      )}
    </div>
  );
}
```

Примечание: проп `stageId` остаётся в типе (его передаёт `ResultStages`), но больше не используется — поэтому не деструктурируется. Пастельные фоны этапов (`BG`-карта) удалены.

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок (нет предупреждения о неиспользуемом `stageId`, т.к. он не в деструктуризации).

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/components/MaterialCard.tsx
git commit -m "feat(style): тёмные карточки материалов + мигающая каретка при стриминге"
```

---

### Task 9: Перекрасить `ResultStages.tsx` (баннер ошибки + заблокированные этапы)

**Files:**
- Modify: `packaging-generator/src/components/ResultStages.tsx:88-124` (заменить блок `return (...)`)

- [ ] **Step 1: Заменить блок `return (...)` (строки 88–124) целиком**

```tsx
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      {error && (
        <div className="fi rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
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
            <div key={stage.id} className="fi rounded-[20px] border border-border bg-card p-5">
              <h3 className="flex items-center gap-2 font-display font-bold text-muted">
                🔒 {stage.title}
              </h3>
              <p className="mt-1 text-sm text-muted">{stage.lockedReason}</p>
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
```

- [ ] **Step 2: Проверка линта**

Run: `npm run lint`
Expected: без ошибок.

- [ ] **Step 3: Коммит**

```bash
git add packaging-generator/src/components/ResultStages.tsx
git commit -m "feat(style): тёмный стиль экрана результатов и заблокированных этапов"
```

---

### Task 10: Финальная проверка (тесты, сборка, визуал)

**Files:** —

- [ ] **Step 1: Прогнать существующие тесты**

Run: `npm run test`
Expected: все 17 тестов зелёные (логика не менялась).

- [ ] **Step 2: Чистая сборка**

Run: `npm run build`
Expected: сборка без ошибок.

- [ ] **Step 3: Живая визуальная проверка**

Run: `npm run dev`, открыть http://localhost:3000.
Проверить вживую:
- Тёмная тема, фиолетовый акцент, шрифт Oswald в заголовках, логотип «АП» в шапке.
- Дым рождается от движения мыши и тает в покое; на кнопке «Дальше»/«Принять» — свечение при наведении.
- Карточки этапов плавно появляются (`.fi`); во время генерации в конце текста мигает фиолетовая каретка.
- Текст результатов читается поверх дыма (карточки на плотном фоне).
- Поставить рядом с aiprohar.ru — смотрится как один продукт.

- [ ] **Step 4: Проверка доступности (reduced-motion)**

В DevTools включить эмуляцию `prefers-reduced-motion: reduce`, обновить страницу.
Expected: дым не запускается, появление карточек и мигание каретки отключены, интерфейс полностью читаем.

- [ ] **Step 5: Финальный коммит (если были мелкие правки на проверке)**

```bash
git add -A packaging-generator/
git commit -m "chore(style): финальная проверка фирменного стиля генератора"
```

---

## Self-Review

**Покрытие спецификации:**
- Источник стиля `brand-tokens.css` → Task 1. ✓
- `@theme` + body + слой компонентов + зерно/скроллбар/фокус → Task 2. ✓
- Oswald + системный шрифт → Task 1 (`--font-body`) + Task 3 (Oswald). ✓
- `fluid.js` + `FluidBackground` → Task 4 + Task 5. ✓
- Свечение кнопок (sglow/srise) → Task 2. ✓
- Зерно + скроллбар → Task 2. ✓
- Плавное появление `.fi` → Task 2 (CSS) + Tasks 7/8/9 (применение). ✓
- Мигающая каретка → Task 2 (CSS) + Task 8 (применение). ✓
- Доступность (reduced-motion) → Task 2 (CSS-guard) + Task 5 (эффект не монтируется) + Task 10 Step 4. ✓
- Читаемость (плотные карточки `--card-solid`) → Tasks 7/8. ✓
- Логотип + favicon → Task 3 + Task 4 + Task 6. ✓
- Перекраска 4 экранов → Tasks 6/7/8/9. ✓
- Логика и 17 тестов не трогаются → подтверждено Task 10 Step 1. ✓

**Согласованность типов:** проп `stageId` остаётся в типе `MaterialCard` и передаётся из `ResultStages` (Task 9), просто не деструктурируется (Task 8) — расхождений нет. Классы `.btn`, `.btn-primary`, `.btn-mini`, `.fi`, `.caret` и утилиты `bg-bg`, `text-text`, `text-muted`, `bg-card-solid`, `bg-accent`, `border-border-p`, `font-display` определены в Tasks 1–2 и используются в Tasks 6–9 одинаково. ✓

**Заглушек нет:** весь код приведён полностью.
