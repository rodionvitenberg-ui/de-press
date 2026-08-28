import { describe, expect, it } from "vitest";
import { en } from "./messages/en";
import { applyFlat, catalogHash, flattenMessages, fmt } from "./flatten";

describe("fmt", () => {
  it("replaces {count}", () => {
    expect(fmt("{count} unread", { count: 3 })).toBe("3 unread");
  });
});

describe("flattenMessages", () => {
  it("round-trips the English catalog strings", () => {
    const flat = flattenMessages(en);
    expect(flat["nav.feed"]).toBe("Feed");
    expect(flat["antiPanic.groundSteps.0"]).toBeTruthy();
    const back = applyFlat(en, flat);
    expect(flattenMessages(back)).toEqual(flat);
  });

  it("hash is stable for the same catalog", () => {
    const a = catalogHash(flattenMessages(en));
    const b = catalogHash(flattenMessages(en));
    expect(a).toBe(b);
    expect(a.length).toBeGreaterThan(0);
  });
});
