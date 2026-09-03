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
import {
  applyTelegramTheme,
  getTelegramWebApp,
  telegramPreferredTheme,
} from "@/core/host/telegram";

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
  // Mini App host: follow Telegram color scheme when available.
  const tg = telegramPreferredTheme();
  if (tg) return tg;
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

function applyTelegramChrome(color: string): void {
  const wa = getTelegramWebApp();
  if (!wa) return;
  try {
    wa.setHeaderColor?.(color);
    wa.setBackgroundColor?.(color);
    wa.setBottomBarColor?.(color);
  } catch {
    /* older clients */
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
    const wa = window.Telegram?.WebApp;
    if (wa) {
      try {
        wa.onEvent("themeChanged", sync);
      } catch {
        /* ignore */
      }
    }
    return () => {
      media.removeEventListener("change", sync);
      if (wa) {
        try {
          wa.offEvent("themeChanged", sync);
        } catch {
          /* ignore */
        }
      }
    };
  }, []);

  const theme: ThemeId = mode === "auto" ? autoTheme(systemAppearance) : mode;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    const color = themeById(theme).themeColor;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", color);
    }
    if (mode === "auto") {
      const wa = getTelegramWebApp();
      if (wa) applyTelegramTheme(wa);
      if (meta) meta.setAttribute("content", color);
      return;
    }
    applyTelegramChrome(color);
    const wa = getTelegramWebApp();
    if (!wa) return;
    const keepExplicitChrome = () => applyTelegramChrome(color);
    try {
      wa.onEvent("themeChanged", keepExplicitChrome);
    } catch {
      /* ignore */
    }
    return () => {
      try {
        wa.offEvent("themeChanged", keepExplicitChrome);
      } catch {
        /* ignore */
      }
    };
  }, [theme, mode]);

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
