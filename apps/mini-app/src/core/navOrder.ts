/** Sidebar order / visibility — local-only (device preference). */

export type NavKey =
  | "feed"
  | "chat"
  | "help"
  | "patterns"
  | "therapy"
  | "helper";

export const DEFAULT_NAV_ORDER: NavKey[] = [
  "feed",
  "chat",
  "help",
  "patterns",
  "therapy",
  "helper",
];

const STORAGE_KEY = "depress:nav-order-v1";

export interface NavPrefs {
  order: NavKey[];
  /** Keys hidden by the user (helper may also be role-gated). */
  hidden: NavKey[];
}

function isNavKey(v: unknown): v is NavKey {
  return (
    v === "feed" ||
    v === "chat" ||
    v === "help" ||
    v === "patterns" ||
    v === "therapy" ||
    v === "helper"
  );
}

export function defaultNavPrefs(): NavPrefs {
  return { order: [...DEFAULT_NAV_ORDER], hidden: [] };
}

export function readNavPrefs(): NavPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultNavPrefs();
    const parsed = JSON.parse(raw) as Partial<NavPrefs>;
    const order = Array.isArray(parsed.order)
      ? parsed.order.filter(isNavKey)
      : [];
    const hidden = Array.isArray(parsed.hidden)
      ? parsed.hidden.filter(isNavKey)
      : [];

    // Merge missing keys from default
    const seen = new Set(order);
    for (const k of DEFAULT_NAV_ORDER) {
      if (!seen.has(k)) order.push(k);
    }

    return { order, hidden };
  } catch {
    return defaultNavPrefs();
  }
}

export function writeNavPrefs(prefs: NavPrefs): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    /* ignore */
  }
}

export function moveNavKey(
  order: NavKey[],
  key: NavKey,
  dir: -1 | 1,
): NavKey[] {
  const idx = order.indexOf(key);
  if (idx < 0) return order;
  const next = idx + dir;
  if (next < 0 || next >= order.length) return order;
  const copy = [...order];
  const tmp = copy[idx]!;
  copy[idx] = copy[next]!;
  copy[next] = tmp;
  return copy;
}
