import { afterEach, describe, expect, it } from "vitest";
import {
  browserTranslateSupport,
  translateFlatInBrowser,
  type BrowserTranslatorCtor,
} from "./clientTranslate";

const flat = { "nav.feed": "Feed", "nav.chat": "Chat", empty: "" };

function installTranslator(ctor: BrowserTranslatorCtor | undefined): void {
  if (ctor === undefined) {
    delete (globalThis as { window?: unknown }).window;
  } else {
    (globalThis as { window?: unknown }).window = { Translator: ctor };
  }
}

function fakeCtor(
  availability: "unavailable" | "available",
  translate: (text: string) => Promise<string> = async (t: string) => `T:${t}`,
): BrowserTranslatorCtor {
  return {
    availability: () => availability,
    create: async () => ({ translate }),
  };
}

afterEach(() => installTranslator(undefined));

describe("browserTranslateSupport", () => {
  it("is unsupported without the Translator API", () => {
    installTranslator(undefined);
    expect(browserTranslateSupport("de")).toBe("unsupported");
  });

  it("is unavailable for pairs the browser cannot translate", () => {
    installTranslator(fakeCtor("unavailable"));
    expect(browserTranslateSupport("kk")).toBe("unavailable");
  });

  it("is available when the pair exists", () => {
    installTranslator(fakeCtor("available"));
    expect(browserTranslateSupport("de")).toBe("available");
  });

  it("survives a throwing availability call", () => {
    installTranslator({
      availability: () => {
        throw new Error("boom");
      },
      create: async () => ({ translate: async (t) => t }),
    });
    expect(browserTranslateSupport("de")).toBe("unsupported");
  });
});

describe("translateFlatInBrowser", () => {
  it("translates every non-empty value and keeps keys", async () => {
    installTranslator(fakeCtor("available"));
    const out = await translateFlatInBrowser(flat, "de");
    expect(out).toEqual({ "nav.feed": "T:Feed", "nav.chat": "T:Chat", empty: "" });
  });

  it("returns null when the API is missing or the pair is unavailable", async () => {
    installTranslator(undefined);
    expect(await translateFlatInBrowser(flat, "de")).toBeNull();
    installTranslator(fakeCtor("unavailable"));
    expect(await translateFlatInBrowser(flat, "kk")).toBeNull();
  });

  it("returns null if any string fails mid-way (no mixed-language catalog)", async () => {
    let calls = 0;
    installTranslator(
      fakeCtor("available", async (t) => {
        calls += 1;
        if (calls > 1) throw new Error("model failed");
        return `T:${t}`;
      }),
    );
    expect(await translateFlatInBrowser(flat, "de")).toBeNull();
  });

  it("returns null when create() fails (model download refused)", async () => {
    installTranslator({
      availability: () => "available",
      create: async () => {
        throw new Error("download aborted");
      },
    });
    expect(await translateFlatInBrowser(flat, "de")).toBeNull();
  });

  it("keeps the source value when the model returns an empty string", async () => {
    installTranslator(fakeCtor("available", async () => "  "));
    const out = await translateFlatInBrowser({ "nav.feed": "Feed" }, "de");
    expect(out).toEqual({ "nav.feed": "Feed" });
  });
});