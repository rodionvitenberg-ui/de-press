import { describe, expect, it } from "vitest";
import {
  THEMES,
  autoTheme,
  isThemeId,
  parseStoredMode,
  themeById,
} from "@de-press/theme";

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
