import { describe, it, expect } from "vitest";
import { VARIANTS, modifierInstruction, type VariantId } from "./variants";

describe("controlled variants", () => {
  it("три варианта с человекочитаемыми ярлыками", () => {
    expect(VARIANTS.map((v) => v.id)).toEqual(["shorter", "bolder", "simpler"]);
    for (const v of VARIANTS) expect(v.label.length).toBeGreaterThan(0);
  });

  it("инструкция модификатора непустая и содержательная", () => {
    const ids: VariantId[] = ["shorter", "bolder", "simpler"];
    for (const id of ids) {
      expect(modifierInstruction(id).length).toBeGreaterThan(10);
    }
    expect(modifierInstruction("shorter")).toContain("короче");
    expect(modifierInstruction("bolder")).toContain("дерз");
    expect(modifierInstruction("simpler")).toContain("прост");
  });
});
