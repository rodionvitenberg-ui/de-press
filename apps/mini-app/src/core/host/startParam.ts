/**
 * Telegram Mini App start_param → app routes.
 *
 * Links:
 *   https://t.me/<bot>?startapp=<param>
 *   https://t.me/<bot>/<app>?startapp=<param>
 *
 * Param is also available as:
 *   Telegram.WebApp.initDataUnsafe.start_param
 *   URL ?tgWebAppStartParam=  (Telegram injects)
 *   URL ?startapp=            (dev / soft-notify convenience)
 *
 * Allowed by Telegram: A–Z a–z 0–9 _ - , max 64 chars.
 */

import { getTelegramWebApp } from "./telegram";

const APPLIED_KEY = "depress:start_param_applied";

/** UUID (with or without hyphens) after a prefix. */
const UUID_RE =
  /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;

export interface StartTarget {
  /** In-app path including leading slash. */
  path: string;
  /** Enter Anti-Panic after navigation. */
  enterAntiPanic?: boolean;
  /** Original param (for logging / once-only). */
  param: string;
}

/**
 * Read start param from TG host or query string (browser/dev).
 * Returns empty string if none.
 */
export function readStartParam(): string {
  const wa = getTelegramWebApp();
  const fromTg = (wa?.initDataUnsafe?.start_param || "").trim();
  if (fromTg) return fromTg.slice(0, 64);

  if (typeof window === "undefined") return "";

  try {
    const q = new URLSearchParams(window.location.search);
    const fromQuery =
      q.get("tgWebAppStartParam") ||
      q.get("startapp") ||
      q.get("start_param") ||
      "";
    return fromQuery.trim().slice(0, 64);
  } catch {
    return "";
  }
}

function normalizeUuid(raw: string): string | null {
  const s = raw.trim();
  if (!UUID_RE.test(s)) return null;
  // Insert hyphens if compact 32-hex
  if (!s.includes("-") && s.length === 32) {
    return [
      s.slice(0, 8),
      s.slice(8, 12),
      s.slice(12, 16),
      s.slice(16, 20),
      s.slice(20),
    ]
      .join("-")
      .toLowerCase();
  }
  return s.toLowerCase();
}

/**
 * Map start_param to a route. Unknown / empty → null (no redirect).
 *
 * Catalog:
 *   feed | home              → /feed
 *   new | feed_new | write   → /feed/new
 *   story_<uuid> | s_<uuid>  → /feed/<uuid>
 *   chat | chats | dialogues → /chat
 *   chat_<uuid> | d_<uuid> | dialogue_<uuid> → /chat/<uuid>
 *   notifications | notify | inbox → /notifications
 *   patterns | mood          → /patterns
 *   help | safety | crisis   → /help
 *   help_wait | wait         → /help/wait
 *   help_ai                  → /help/ai
 *   helper | helpers         → /helper
 *   panic | antipanic | anti_panic | meh → /help + Anti-Panic
 */
export function resolveStartParam(param: string): StartTarget | null {
  const raw = (param || "").trim();
  if (!raw) return null;

  const key = raw.toLowerCase();

  // prefix_id forms
  const storyMatch = key.match(/^(?:story|s)[_-](.+)$/);
  if (storyMatch) {
    const id = normalizeUuid(storyMatch[1]);
    if (id) return { path: `/feed/${id}`, param: raw };
  }

  const chatMatch = key.match(/^(?:chat|dialogue|d)[_-](.+)$/);
  if (chatMatch) {
    const id = normalizeUuid(chatMatch[1]);
    if (id) return { path: `/chat/${id}`, param: raw };
  }

  switch (key) {
    case "feed":
    case "home":
    case "stories":
      return { path: "/feed", param: raw };
    case "new":
    case "feed_new":
    case "write":
    case "compose":
      return { path: "/feed/new", param: raw };
    case "chat":
    case "chats":
    case "dialogues":
    case "dialogue":
      return { path: "/chat", param: raw };
    case "notifications":
    case "notify":
    case "inbox":
    case "n":
      return { path: "/notifications", param: raw };
    case "patterns":
    case "mood":
    case "zk":
      return { path: "/patterns", param: raw };
    case "help":
    case "safety":
    case "crisis":
      return { path: "/help", param: raw };
    case "help_wait":
    case "help-wait":
    case "wait":
      return { path: "/help/wait", param: raw };
    case "help_ai":
    case "help-ai":
      return { path: "/help/ai", param: raw };
    case "helper":
    case "helpers":
      return { path: "/helper", param: raw };
    case "panic":
    case "antipanic":
    case "anti_panic":
    case "anti-panic":
    case "meh":
      return { path: "/help", enterAntiPanic: true, param: raw };
    default:
      return null;
  }
}

/** Session-once guard so we don't re-apply on every remount. */
export function wasStartParamApplied(param: string): boolean {
  if (!param) return true;
  try {
    return sessionStorage.getItem(APPLIED_KEY) === param;
  } catch {
    return false;
  }
}

export function markStartParamApplied(param: string): void {
  try {
    sessionStorage.setItem(APPLIED_KEY, param);
  } catch {
    /* ignore */
  }
}

/** Strip startapp query keys so refresh doesn't re-trigger via browser URL. */
export function stripStartParamFromUrl(): void {
  if (typeof window === "undefined") return;
  try {
    const url = new URL(window.location.href);
    let changed = false;
    for (const key of ["startapp", "start_param", "tgWebAppStartParam"]) {
      if (url.searchParams.has(key)) {
        url.searchParams.delete(key);
        changed = true;
      }
    }
    if (changed) {
      window.history.replaceState(
        window.history.state,
        "",
        url.pathname + url.search + url.hash,
      );
    }
  } catch {
    /* ignore */
  }
}

export const ENTER_ANTI_PANIC_EVENT = "depress:enter-anti-panic";

export function requestEnterAntiPanic(): void {
  try {
    window.localStorage.setItem("depress_anti_panic", "1");
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new CustomEvent(ENTER_ANTI_PANIC_EVENT));
}
