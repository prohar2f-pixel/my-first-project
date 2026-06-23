import { describe, it, expect } from "vitest";
import { buildSystemPrompt, buildStagePrompt } from "./prompts";
import type { Brief } from "../onboarding/questions";

const brief: Brief = {
  niche: "Психолог, работаю с выгоранием",
  audience: "Мамы в декрете",
  result: "Выходят из выгорания за 6 недель",
  method: "6-недельная программа",
  difference: "Работаю по протоколу",
  product: "Курс, 15 000 ₽",
  tone: "Тепло, без эзотерики",
};

describe("prompt building", () => {
  it("system-промпт задаёт роль маркетолога и русский язык", () => {
    const sys = buildSystemPrompt();
    expect(sys.toLowerCase()).toContain("маркетолог");
    expect(sys.toLowerCase()).toContain("русск");
  });

  it("промпт оффера включает все поля брифа", () => {
    const p = buildStagePrompt("offer", brief);
    for (const value of Object.values(brief)) {
      expect(p).toContain(value);
    }
  });

  it("промпт лендинга опирается на принятый оффер", () => {
    const p = buildStagePrompt("landing", brief, { acceptedOffer: "Мой оффер" });
    expect(p).toContain("Мой оффер");
  });

  it("модификатор добавляется в промпт при пере-генерации", () => {
    const p = buildStagePrompt("offer", brief, {
      modifier: "Сделай заметно короче",
    });
    expect(p).toContain("Сделай заметно короче");
  });
});
