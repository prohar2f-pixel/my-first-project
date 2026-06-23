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
