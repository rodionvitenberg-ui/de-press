import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  THEME_IDS,
  THEMES,
  autoTheme,
  isThemeId,
  parseStoredMode,
  themeById,
} from "@de-press/theme";

const REQUIRED_COLOR_TOKENS = [
  "--bg-main",
  "--bg-surface",
  "--bg-elevated",
  "--bg-sidebar",
  "--bg-chat",
  "--bg-input",
  "--bg-hover",
  "--bg-active",
  "--bg-bubble-me",
  "--bg-bubble-them",
  "--text-primary",
  "--text-muted",
  "--text-bubble",
  "--text-bubble-muted",
  "--accent-hope",
  "--accent-hope-soft",
  "--accent-hope-mid",
  "--accent-panic",
  "--on-accent-hope",
  "--on-accent-panic",
  "--border-subtle",
  "--border-soft",
  "--shadow-elev-1",
  "--shadow-elev-2",
  "--shadow-cloud",
  "--focus-ring",
  "--chat-pattern-a",
  "--chat-pattern-b",
  "--chat-pattern-c",
  "--chat-wallpaper",
  "--chat-wallpaper-size",
  "--chat-wallpaper-pos",
] as const;

function readThemeTokensCss(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return readFileSync(
    join(here, "../../../../packages/theme/src/tokens.css"),
    "utf8",
  );
}

/** First `{...}` block after `[data-theme="<id>"]` (no nested braces in tokens.css). */
function themeBlock(css: string, id: string): string {
  const marker = `[data-theme="${id}"]`;
  const idx = css.indexOf(marker);
  if (idx === -1) return "";
  const open = css.indexOf("{", idx);
  if (open === -1) return "";
  const close = css.indexOf("}", open);
  if (close === -1) return "";
  return css.slice(open, close + 1);
}

describe("parseStoredMode", () => {
  it("keeps a stored named theme such as aurora", () => {
    expect(parseStoredMode("aurora")).toBe("aurora");
  });

  it("falls back to auto for unknown values", () => {
    expect(parseStoredMode("nope")).toBe("auto");
  });

  it("keeps auto and treats null as auto", () => {
    expect(parseStoredMode("auto")).toBe("auto");
    expect(parseStoredMode(null)).toBe("auto");
  });
});

describe("theme registry", () => {
  it("maps auto appearance to the matching theme id", () => {
    expect(autoTheme("light")).toBe("light");
    expect(autoTheme("dark")).toBe("dark");
  });

  it("resolves auto + light appearance to light, not aurora", () => {
    expect(autoTheme("light")).toBe("light");
    expect(autoTheme("light")).not.toBe("aurora");
  });

  it("recognizes known theme ids and rejects unknown ones", () => {
    expect(isThemeId("aurora")).toBe(true);
    expect(isThemeId("sepia")).toBe(false);
  });

  it("gives every theme a themeColor and colorScheme", () => {
    for (const theme of THEMES) {
      expect(theme.themeColor).toBeTruthy();
      expect(theme.colorScheme === "dark" || theme.colorScheme === "light").toBe(
        true,
      );
      expect(themeById(theme.id)).toEqual(theme);
    }
  });

  it("has exactly one theme per autoAppearance", () => {
    const appearances = THEMES.map((t) => t.autoAppearance).filter(
      (v): v is NonNullable<typeof v> => v != null,
    );
    expect(appearances).toEqual(["dark", "light"]);
    expect(new Set(appearances).size).toBe(appearances.length);
  });
});

describe("theme tokens.css palettes", () => {
  it("defines the full color token set for every THEME_IDS entry", () => {
    const css = readThemeTokensCss();

    for (const id of THEME_IDS) {
      expect(css).toContain(`:root[data-theme="${id}"]`);
      const block = themeBlock(css, id);
      expect(block.length).toBeGreaterThan(0);
      for (const token of REQUIRED_COLOR_TOKENS) {
        expect(block, `${id} missing ${token}`).toContain(`${token}:`);
      }
    }
  });
});
