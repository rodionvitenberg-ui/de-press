/**
 * Client-side fallback: translate the flat UI catalog with the browser's
 * built-in on-device Translator API (Chrome 138+ / Edge, free, no API key).
 *
 * Used only when the server refuses the catalog (no server-side translator
 * configured → honest 400). Covers Chrome's language pair list; for pairs the
 * browser cannot translate the result is null and the UI keeps its honest
 * "translation unavailable" marker.
 *
 * Chrome docs: https://developer.chrome.com/docs/ai/translator-api
 */

type TranslatorAvailability =
  | "unavailable"
  | "downloadable"
  | "downloading"
  | "available";

interface BrowserTranslator {
  translate(text: string): Promise<string>;
}

export interface BrowserTranslatorCtor {
  availability(options: {
    sourceLanguage: string;
    targetLanguage: string;
  }): Promise<TranslatorAvailability> | TranslatorAvailability;
  create(options: {
    sourceLanguage: string;
    targetLanguage: string;
  }): Promise<BrowserTranslator>;
}

declare global {
  interface Window {
    Translator?: BrowserTranslatorCtor;
  }
}

export type BrowserTranslateSupport =
  | "unsupported" // no Translator API (Firefox, Safari, older Chrome, webviews)
  | "unavailable" // API exists but the en → target pair is not in the browser
  | "available"; // usable (may download the on-device model first)

export function browserTranslateSupport(target: string): BrowserTranslateSupport {
  const ctor = globalThis.window?.Translator;
  if (!ctor) return "unsupported";
  try {
    const state = ctor.availability({
      sourceLanguage: "en",
      targetLanguage: (target || "").slice(0, 8).toLowerCase(),
    });
    if (state instanceof Promise) {
      // Sync call was expected; an async result can't be classified here.
      return "available";
    }
    return state === "unavailable" ? "unavailable" : "available";
  } catch {
    return "unsupported";
  }
}

/**
 * Translate every non-empty value of the flat catalog. Returns null on any
 * failure — a partial catalog would mix languages, the honest marker is
 * better than a hybrid.
 */
export async function translateFlatInBrowser(
  flat: Record<string, string>,
  target: string,
): Promise<Record<string, string> | null> {
  if (browserTranslateSupport(target) !== "available") return null;
  const ctor = globalThis.window!.Translator!;
  let translator: BrowserTranslator;
  try {
    translator = await ctor.create({
      sourceLanguage: "en",
      targetLanguage: target.slice(0, 8).toLowerCase(),
    });
  } catch {
    return null;
  }
  const out: Record<string, string> = {};
  try {
    for (const [key, value] of Object.entries(flat)) {
      if (!value.trim()) {
        out[key] = value;
        continue;
      }
      const translated = await translator.translate(value);
      out[key] = typeof translated === "string" && translated.trim() ? translated : value;
    }
  } catch {
    return null;
  }
  return out;
}