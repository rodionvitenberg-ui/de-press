import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { telegramPreferredTheme } from "@/core/host/telegram";

export type ThemeMode = "auto" | "dark" | "light";
export type ResolvedTheme = "dark" | "light";

const STORAGE_KEY = "depress:theme-mode";

interface ThemeContextValue {
  mode: ThemeMode;
  theme: ResolvedTheme;
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function resolveSystemTheme(): ResolvedTheme {
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
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "auto" || raw === "dark" || raw === "light") return raw;
  } catch {
    /* ignore */
  }
  return "auto";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(readStoredMode);
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(resolveSystemTheme);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: light)");
    const sync = () => setSystemTheme(resolveSystemTheme());
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

  const theme: ResolvedTheme = mode === "auto" ? systemTheme : mode;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", theme === "dark" ? "#0c0e12" : "#f3efe9");
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