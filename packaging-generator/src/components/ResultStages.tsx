"use client";

import { useEffect, useRef, useState } from "react";
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
  const textsRef = useRef<Record<string, string>>({});
  const [streaming, setStreaming] = useState<StageId | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef<string>(crypto.randomUUID()).current;
  const didStart = useRef(false);

  function updateTexts(updater: (t: Record<string, string>) => Record<string, string>) {
    setTexts((t) => {
      const next = updater(t);
      textsRef.current = next;
      return next;
    });
  }

  async function generate(stage: StageId, modifier?: VariantId) {
    setError(null);
    setStreaming(stage);
    const previous = textsRef.current[stage] ?? "";
    updateTexts((t) => ({ ...t, [stage]: "" }));
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stage,
          brief,
          acceptedOffer: textsRef.current.offer,
          acceptedLanding: textsRef.current.landing,
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
        updateTexts((t) => ({ ...t, [stage]: acc }));
      }
    } catch {
      setError("Не получилось сгенерировать. Попробуй ещё раз.");
      updateTexts((t) => ({ ...t, [stage]: previous }));
    } finally {
      setStreaming(null);
    }
  }

  // Auto-generate offer once on mount — latch prevents StrictMode double-invoke
  useEffect(() => {
    if (didStart.current) return;
    didStart.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
    generate("offer");
  }, []);

  function accept(stage: StageId) {
    const updated = accepted.includes(stage) ? accepted : [...accepted, stage];
    setAccepted(updated);
    const nxt = nextStage(stage);
    if (nxt && !textsRef.current[nxt]) generate(nxt);
    // Best-effort background save — never blocks or throws in the UI
    fetch("/api/packages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, brief, materials: textsRef.current }),
    }).catch(() => {});
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
