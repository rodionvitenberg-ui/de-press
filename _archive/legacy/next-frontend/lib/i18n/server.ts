import { cookies } from "next/headers";
import { DEFAULT_LOCALE, LOCALE_COOKIE, type Locale } from "./types";

/**
 * Resolve the locale on the server from the `depress_locale` cookie.
 * Falls back to the default locale.
 */
export async function getServerLocale(): Promise<Locale> {
  const store = await cookies();
  const cookie = store.get(LOCALE_COOKIE)?.value;
  if (cookie === "ru" || cookie === "en") {
    return cookie;
  }
  return DEFAULT_LOCALE;
}