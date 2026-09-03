/**
 * Telegram Mini App host bridge.
 * Docs: https://core.telegram.org/bots/webapps
 */

import { themeById } from "@de-press/theme";

export type TelegramColorScheme = "light" | "dark";

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
  header_bg_color?: string;
  accent_text_color?: string;
  section_bg_color?: string;
  section_header_text_color?: string;
  subtitle_text_color?: string;
  destructive_text_color?: string;
  bottom_bar_bg_color?: string;
  section_separator_color?: string;
}

export interface TelegramWebAppUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

/** Subset of Telegram.WebApp used by de-press. */
export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: TelegramWebAppUser;
    start_param?: string;
    auth_date?: number;
    query_id?: string;
  };
  version: string;
  platform: string;
  colorScheme: TelegramColorScheme;
  themeParams: TelegramThemeParams;
  isExpanded: boolean;
  viewportStableHeight: number;
  ready: () => void;
  expand: () => void;
  close: () => void;
  disableVerticalSwipes?: () => void;
  enableVerticalSwipes?: () => void;
  requestFullscreen?: () => void;
  exitFullscreen?: () => void;
  setHeaderColor?: (color: "bg_color" | "secondary_bg_color" | string) => void;
  setBackgroundColor?: (color: string) => void;
  setBottomBarColor?: (color: string) => void;
  onEvent: (eventType: string, handler: () => void) => void;
  offEvent: (eventType: string, handler: () => void) => void;
  BackButton: {
    isVisible: boolean;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
    notificationOccurred: (type: "error" | "success" | "warning") => void;
    selectionChanged: () => void;
  };
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export function getTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") return null;
  const wa = window.Telegram?.WebApp;
  if (!wa || typeof wa.initData !== "string") return null;
  return wa;
}

/** True when running inside Telegram Mini App with non-empty signed initData. */
export function isTelegramHost(): boolean {
  const wa = getTelegramWebApp();
  return Boolean(wa && wa.initData.length > 0);
}

/**
 * Mark Mini App ready, expand, sync basic chrome.
 * Safe no-op outside Telegram.
 */
export function bootstrapTelegramHost(): TelegramWebApp | null {
  const wa = getTelegramWebApp();
  if (!wa) return null;

  try {
    wa.ready();
  } catch {
    /* ignore */
  }
  try {
    wa.expand();
  } catch {
    /* ignore */
  }

  document.documentElement.dataset.host = "telegram";
  document.documentElement.dataset.tgPlatform = wa.platform || "";

  applyTelegramTheme(wa);

  const onTheme = () => applyTelegramTheme(wa);
  try {
    wa.onEvent("themeChanged", onTheme);
  } catch {
    /* ignore */
  }

  return wa;
}

/** Map Telegram theme to de-press data-theme when user mode is auto. */
export function applyTelegramTheme(wa: TelegramWebApp = getTelegramWebApp()!): void {
  if (!wa) return;
  const scheme = wa.colorScheme === "light" ? "light" : "dark";
  // Host hint for CSS; ThemeProvider still owns data-theme when mode is forced.
  document.documentElement.dataset.tgColorScheme = scheme;

  const bg =
    wa.themeParams.bg_color ||
    (scheme === "dark"
      ? themeById("dark").themeColor
      : themeById("light").themeColor);
  try {
    wa.setHeaderColor?.(bg);
    wa.setBackgroundColor?.(bg);
    wa.setBottomBarColor?.(bg);
  } catch {
    /* older clients */
  }

  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", bg);
}

/** Prefer TG color scheme when ThemeMode is auto. */
export function telegramPreferredTheme(): "light" | "dark" | null {
  const wa = getTelegramWebApp();
  if (!wa || !wa.initData) return null;
  return wa.colorScheme === "light" ? "light" : "dark";
}

/** Disable swipe-to-close during Anti-Panic if API available. */
export function setTelegramVerticalSwipes(enabled: boolean): void {
  const wa = getTelegramWebApp();
  if (!wa) return;
  try {
    if (enabled) wa.enableVerticalSwipes?.();
    else wa.disableVerticalSwipes?.();
  } catch {
    /* ignore */
  }
}
