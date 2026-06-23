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
    "Сделай проще и понятнее: убери сложные слова и термины, простые фразы для обычного человека. Краткость.",
};

export function modifierInstruction(id: VariantId): string {
  return INSTRUCTIONS[id];
}
