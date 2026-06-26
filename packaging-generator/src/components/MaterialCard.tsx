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
