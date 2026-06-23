import { describe, it, expect } from "vitest";
import { QUESTIONS, isBriefComplete, type Brief } from "./questions";

describe("onboarding questions", () => {
  it("содержит ровно 7 вопросов с уникальными id", () => {
    expect(QUESTIONS).toHaveLength(7);
    const ids = QUESTIONS.map((q) => q.id);
    expect(new Set(ids).size).toBe(7);
  });

  it("у каждого вопроса есть текст, подсказка и пример-плейсхолдер", () => {
    for (const q of QUESTIONS) {
      expect(q.label.length).toBeGreaterThan(0);
      expect(q.hint.length).toBeGreaterThan(0);
      expect(q.placeholder.length).toBeGreaterThan(0);
    }
  });

  it("бриф полон, только когда заполнены все вопросы непустыми ответами", () => {
    const empty = {} as Brief;
    expect(isBriefComplete(empty)).toBe(false);

    const full = Object.fromEntries(
      QUESTIONS.map((q) => [q.id, "ответ"]),
    ) as Brief;
    expect(isBriefComplete(full)).toBe(true);

    const partial = { ...full, [QUESTIONS[0].id]: "  " };
    expect(isBriefComplete(partial)).toBe(false);
  });
});
