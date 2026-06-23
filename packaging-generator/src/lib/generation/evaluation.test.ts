import { describe, it, expect } from "vitest";
import {
  EvaluationSchema,
  buildEvaluationPrompt,
  STRENGTH_LABELS,
} from "./evaluation";

describe("offer evaluation", () => {
  it("шкала силы — грубая (3 градации), без псевдоточных баллов", () => {
    expect(STRENGTH_LABELS).toEqual(["низкий", "средний", "сильный"]);
  });

  it("схема требует силу, слабое место и как улучшить", () => {
    const ok = EvaluationSchema.safeParse({
      strength: "средний",
      weakSpot: "Неясен результат",
      howToImprove: "Уточнить срок",
    });
    expect(ok.success).toBe(true);

    const bad = EvaluationSchema.safeParse({ strength: "7.8" });
    expect(bad.success).toBe(false);
  });

  it("промпт оценки содержит сам оффер", () => {
    const p = buildEvaluationPrompt("Помогаю мамам выйти из выгорания");
    expect(p).toContain("Помогаю мамам выйти из выгорания");
  });
});
