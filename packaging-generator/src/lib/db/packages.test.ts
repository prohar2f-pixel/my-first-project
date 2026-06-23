import { describe, it, expect } from "vitest";
import { rowToPackage } from "./packages";

describe("packages row mapping", () => {
  it("превращает строку БД в объект упаковки", () => {
    const row = {
      session_id: "abc",
      brief: { niche: "Психолог" } as never,
      materials: { offer: "текст" },
      created_at: new Date("2026-06-24T10:00:00Z"),
    };
    const pkg = rowToPackage(row);
    expect(pkg.sessionId).toBe("abc");
    expect(pkg.brief.niche).toBe("Психолог");
    expect(pkg.materials.offer).toBe("текст");
    expect(pkg.createdAt).toBe("2026-06-24T10:00:00.000Z");
  });
});
