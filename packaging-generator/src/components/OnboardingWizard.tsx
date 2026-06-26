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
}
