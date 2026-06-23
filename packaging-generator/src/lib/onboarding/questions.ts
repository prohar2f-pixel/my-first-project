export type QuestionId =
  | "niche"
  | "audience"
  | "result"
  | "method"
  | "difference"
  | "product"
  | "tone";

export interface Question {
  id: QuestionId;
  label: string;
  hint: string;
  placeholder: string;
}

export type Brief = Record<QuestionId, string>;

export const QUESTIONS: Question[] = [
  {
    id: "niche",
    label: "Чем ты занимаешься?",
    hint: "Твоя ниша одной фразой.",
    placeholder: "Психолог, работаю с тревогой и выгоранием",
  },
  {
    id: "audience",
    label: "Кому ты помогаешь?",
    hint: "Твоя аудитория.",
    placeholder: "Мамы 30–40 лет в декрете",
  },
  {
    id: "result",
    label: "Какой результат получает клиент?",
    hint: "Главный итог в 5–8 слов.",
    placeholder: "Выходят из выгорания за 6 недель",
  },
  {
    id: "method",
    label: "Как ты это делаешь?",
    hint: "Метод или формат работы.",
    placeholder: "6-недельная программа мягких ежедневных шагов",
  },
  {
    id: "difference",
    label: "Чем ты отличаешься от других?",
    hint: "Твоя отстройка.",
    placeholder: "Работаю по протоколу, а не по наитию",
  },
  {
    id: "product",
    label: "Что ты продаёшь и за сколько?",
    hint: "Продукт и цена.",
    placeholder: "Консультации + курс, 15 000 ₽",
  },
  {
    id: "tone",
    label: "В каком тоне общаешься?",
    hint: "Голос бренда.",
    placeholder: "Тепло, по-человечески, без эзотерики",
  },
];

export function isBriefComplete(brief: Brief): boolean {
  return QUESTIONS.every((q) => (brief[q.id] ?? "").trim().length > 0);
}
