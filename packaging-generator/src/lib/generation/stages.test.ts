import { describe, it, expect } from "vitest";
import { STAGES, isStageUnlocked, nextStage, type StageId } from "./stages";

describe("stages sequencing", () => {
  it("три этапа в правильном порядке", () => {
    expect(STAGES.map((s) => s.id)).toEqual(["offer", "landing", "emails"]);
  });

  it("первый этап открыт всегда", () => {
    expect(isStageUnlocked("offer", [])).toBe(true);
  });

  it("следующий этап закрыт, пока предыдущий не принят", () => {
    expect(isStageUnlocked("landing", [])).toBe(false);
    expect(isStageUnlocked("landing", ["offer"])).toBe(true);
    expect(isStageUnlocked("emails", ["offer"])).toBe(false);
    expect(isStageUnlocked("emails", ["offer", "landing"])).toBe(true);
  });

  it("nextStage возвращает следующий этап или null на последнем", () => {
    expect(nextStage("offer")).toBe("landing");
    expect(nextStage("landing")).toBe("emails");
    expect(nextStage("emails")).toBeNull();
  });
});
