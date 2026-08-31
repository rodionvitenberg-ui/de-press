/**
 * Hierarchical parent paths for Telegram BackButton (and shared nav helpers).
 */

/** Section roots: no BackButton. */
const SECTION_ROOTS = new Set([
  "/",
  "/feed",
  "/chat",
  "/patterns",
  "/help",
  "/helper",
]);

/**
 * Parent route for hierarchical back.
 * Returns null at section roots (BackButton should hide).
 */
export function parentPath(pathname: string): string | null {
  const path = (pathname || "/").replace(/\/+$/, "") || "/";
  if (SECTION_ROOTS.has(path)) return null;

  // /feed/new | /feed/:id → /feed
  if (path.startsWith("/feed/")) return "/feed";
  // /chat/:id → /chat
  if (path.startsWith("/chat/")) return "/chat";

  // Unknown nested: strip last segment
  const idx = path.lastIndexOf("/");
  if (idx <= 0) return null;
  const parent = path.slice(0, idx) || "/";
  return parent;
}

export function isSectionRoot(pathname: string): boolean {
  return parentPath(pathname) === null;
}
