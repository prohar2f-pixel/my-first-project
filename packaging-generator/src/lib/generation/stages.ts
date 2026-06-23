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
