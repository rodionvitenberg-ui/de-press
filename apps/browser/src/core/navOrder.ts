/** Sidebar order / visibility — local-only (device preference). */

export type NavKey =
  | "feed"
  | "chat"
  | "help"
  | "patterns"
  | "notifications"
  | "helper";

export const DEFAULT_NAV_ORDER: NavKey[] = [
  "feed",
  "chat",
  "help",
  "patterns",
  "notifications",
  "helper",
];

