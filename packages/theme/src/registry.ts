export type ThemeId = "dark" | "light" | "aurora";
export type ThemeMode = "auto" | ThemeId;
export type ColorScheme = "dark" | "light";

export type ThemeDef = {
  id: ThemeId;
  colorScheme: ColorScheme;
  themeColor: string;
  autoAppearance?: ColorScheme;
};

export const THEMES: readonly ThemeDef[] = [
  { id: "dark", colorScheme: "dark", themeColor: "#0c0e12", autoAppearance: "dark" },
  { id: "light", colorScheme: "light", themeColor: "#f3efe9", autoAppearance: "light" },
  { id: "aurora", colorScheme: "dark", themeColor: "#0c101b" },
];

export const THEME_IDS: ThemeId[] = THEMES.map((t) => t.id);

export function isThemeId(v: string): v is ThemeId {
  return (THEME_IDS as string[]).includes(v);
}

export function themeById(id: ThemeId): ThemeDef {
  return THEMES.find((t) => t.id === id)!;
}

export function autoTheme(appearance: ColorScheme): ThemeId {
  return THEMES.find((t) => t.autoAppearance === appearance)?.id ?? "dark";
}

export function parseStoredMode(raw: string | null): ThemeMode {
  if (raw === "auto" || (raw !== null && isThemeId(raw))) return raw;
  return "auto";
}
