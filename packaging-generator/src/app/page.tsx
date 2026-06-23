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
