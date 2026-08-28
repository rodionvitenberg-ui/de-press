import { describe, expect, it } from "vitest";
import { tabletListWidth } from "./listWidth";

describe("tabletListWidth", () => {
  it("caps stored width at 40% of the viewport without raising it", () => {
    expect(tabletListWidth(424, 800)).toBe(320);
    expect(tabletListWidth(280, 1000)).toBe(280);
  });
});
