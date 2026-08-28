import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { ANTI_PANIC_KEY, readAntiPanic, writeAntiPanic } from "./antiPanic";

const mem = new Map<string, string>();

beforeEach(() => {
  mem.clear();
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => mem.get(k) ?? null,
      setItem: (k: string, v: string) => {
        mem.set(k, v);
      },
      removeItem: (k: string) => {
        mem.delete(k);
      },
    },
  });
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { localStorage: globalThis.localStorage },
  });
});


describe("antiPanic storage", () => {
  afterEach(() => {
    try {
      localStorage.removeItem(ANTI_PANIC_KEY);
    } catch {
      /* ignore */
    }
  });

  it("is off by default", () => {
    expect(readAntiPanic()).toBe(false);
  });

  it("reads stored flag", () => {
    localStorage.setItem(ANTI_PANIC_KEY, "1");
    expect(readAntiPanic()).toBe(true);
  });

  it("write true persists, write false clears", () => {
    writeAntiPanic(true);
    expect(localStorage.getItem(ANTI_PANIC_KEY)).toBe("1");
    expect(readAntiPanic()).toBe(true);
    writeAntiPanic(false);
    expect(localStorage.getItem(ANTI_PANIC_KEY)).toBe(null);
    expect(readAntiPanic()).toBe(false);
  });
});
