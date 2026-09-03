import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  autoTheme,
  parseStoredMode,
  themeById,
  type ColorScheme,
  type ThemeId,
  type ThemeMode,
} from "@de-press/theme";

export type { ThemeId, ThemeMode } from "@de-press/theme";
export { THEME_IDS } from "@de-press/theme";
export type ResolvedTheme = ThemeId;

const STORAGE_KEY = "depress:theme-mode";

interface ThemeContextValue {
  mode: ThemeMode;
  theme: ThemeId;
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function resolveSystemAppearance(): ColorScheme {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

function readStoredMode(): ThemeMode {
  try {
    return parseStoredMode(localStorage.getItem(STORAGE_KEY));
  } catch {
    return "auto";
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(readStoredMode);
  const [systemAppearance, setSystemAppearance] = useState<ColorScheme>(
    resolveSystemAppearance,
  );

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: light)");
    const sync = () => setSystemAppearance(resolveSystemAppearance());
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  const theme: ThemeId = mode === "auto" ? autoTheme(systemAppearance) : mode;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.host = "browser";
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", themeById(theme).themeColor);
    }
  }, [theme]);

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({ mode, theme, setMode }),
    [mode, theme, setMode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
