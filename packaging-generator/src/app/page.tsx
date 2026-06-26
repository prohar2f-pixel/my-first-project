"use client";

import { useState } from "react";
import type { Brief } from "@/lib/onboarding/questions";
import { OnboardingWizard } from "@/components/OnboardingWizard";
import { ResultStages } from "@/components/ResultStages";

export default function Home() {
  const [brief, setBrief] = useState<Brief | null>(null);

  return (
    <div className="relative min-h-screen text-text">
      <header className="sticky top-0 z-20 border-b border-white/5 bg-bg/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
          <a href="#" className="flex items-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
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
