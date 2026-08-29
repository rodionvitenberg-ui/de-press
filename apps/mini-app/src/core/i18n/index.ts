import { en } from "./messages/en";
import { ru } from "./messages/ru";
import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  LOCALE_STORAGE_KEY,
  LOCALES,
  type Locale,
  type Messages,
} from "./types";

export type { Locale, Messages };
export {
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  LOCALE_STORAGE_KEY,
  LOCALES,
};

const catalogs: Record<Locale, Messages> = { ru, en };

export function isHandwrittenLocale(
  value: string | null | undefined,
): value is "ru" | "en" {
  return value === "ru" || value === "en";
}

export function isLocale(value: string | null | undefined): value is Locale {
  return value === "ru" || value === "en";
}

export function getMessages(locale: Locale): Messages {
  return catalogs[locale] ?? catalogs[DEFAULT_LOCALE];
}

export function readStoredLocale(): Locale {
  try {
    const fromStorage = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    if (isLocale(fromStorage)) return fromStorage;
  } catch {
    /* ignore */
  }
  const match = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${LOCALE_COOKIE}=`));
  if (match) {
    const value = match.split("=")[1];
    if (isLocale(value)) return value;
  }
  // Mini App: Telegram language_code when no stored preference
  try {
    const tgLang =
      window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code?.toLowerCase() ??
      "";
    if (tgLang.startsWith("en")) return "en";
    if (tgLang.startsWith("ru")) return "ru";
  } catch {
    /* ignore */
  }
  const nav = navigator.language?.toLowerCase() ?? "";
  if (nav.startsWith("en")) return "en";
  return DEFAULT_LOCALE;
}

export function persistLocale(locale: Locale): void {
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    /* ignore */
  }
  const maxAge = 60 * 60 * 24 * 365;
  document.cookie = `${LOCALE_COOKIE}=${locale}; path=/; max-age=${maxAge}; samesite=lax`;
  document.documentElement.lang = locale;
  document.title = getMessages(locale).meta.title;
}
