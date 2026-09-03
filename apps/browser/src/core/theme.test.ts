import { describe, expect, it } from "vitest";
import {
  THEMES,
  autoTheme,
  isThemeId,
  themeById,
} from "@de-press/theme";

describe("theme registry", () => {
  it("maps auto appearance to the matching theme id", () => {
    expect(autoTheme("light")).toBe("light");
    expect(autoTheme("dark")).toBe("dark");
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
