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
