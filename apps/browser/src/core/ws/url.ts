/**
 * WebSocket base URL (no trailing slash).
 * Same-origin via Vite proxy `/ws` → Django, so session cookies apply.
 */
export function buildWsBase(): string {
  if (typeof window === "undefined") {
    return "ws://127.0.0.1:5174";
  }
  const pageProto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${pageProto}//${window.location.host}`;
}
