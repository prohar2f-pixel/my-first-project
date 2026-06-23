import { z } from "zod";

export const STRENGTH_LABELS = ["низкий", "средний", "сильный"] as const;

export const EvaluationSchema = z.object({
  strength: z.enum(STRENGTH_LABELS),
  weakSpot: z.string().min(1),
  howToImprove: z.string().min(1),
});

export type Evaluation = z.infer<typeof EvaluationSchema>;

export function buildEvaluationPrompt(offer: string): string {
  return [
    "Оцени этот оффер эксперта как маркетолог.",
    "",
    `Оффер:\n${offer}`,
    "",
    "Дай: грубую оценку силы (низкий/средний/сильный — без числовых баллов),",
    "одно главное слабое место и один конкретный совет, как его улучшить.",
    "Пиши по-русски, коротко и по делу.",
  ].join("\n");
}
