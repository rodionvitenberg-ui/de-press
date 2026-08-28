/**
 * Host bootstrap: detect Telegram Mini App and establish session.
 */

import { api } from "@/core/api/client";
import type { Me } from "@/core/api/types";
import {
  bootstrapTelegramHost,
  getTelegramWebApp,
  isTelegramHost,
} from "./telegram";

export type AppHostKind = "browser" | "telegram";

export interface HostBootstrapResult {
  host: AppHostKind;
  me: Me | null;
  telegramAuthError: string | null;
}

/**
 * Call once at app start (before or while mounting React).
 * - Browser: no-op auth (anon cookie via later API calls).
 * - Telegram: ready/expand + POST /auth/telegram with initData.
 */
export async function bootstrapHost(): Promise<HostBootstrapResult> {
  if (!isTelegramHost()) {
    document.documentElement.dataset.host = "browser";
    return { host: "browser", me: null, telegramAuthError: null };
  }

  bootstrapTelegramHost();

  const wa = getTelegramWebApp();
  const initData = wa?.initData ?? "";
  if (!initData) {
    return {
      host: "telegram",
      me: null,
      telegramAuthError: "empty_init_data",
    };
  }

  try {
    const me = await api.loginTelegram(initData);
    return { host: "telegram", me, telegramAuthError: null };
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "telegram_auth_failed";
    console.warn("[host] Telegram auth failed:", message);
    return {
      host: "telegram",
      me: null,
      telegramAuthError: message,
    };
  }
}
