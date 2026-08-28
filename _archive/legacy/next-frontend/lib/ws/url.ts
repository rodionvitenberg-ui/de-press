/**
 * Build WebSocket base URL (no trailing slash).
 *
 * Prefer env port/path, but force hostname to match the page so session /
 * depress_anon cookies (bound to localhost OR 127.0.0.1) still apply.
 */
export function buildWsBase(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, "");

  if (typeof window !== "undefined") {
    const pageHost = window.location.hostname;
    const pageProto = window.location.protocol === "https:" ? "wss:" : "ws:";

    if (explicit) {
      try {
        const u = new URL(explicit);
        u.protocol = pageProto;
        u.hostname = pageHost;
        return u.origin;
      } catch {
        return explicit;
      }
    }

    // Default Daphne port from project convention
    return `${pageProto}//${pageHost}:8005`;
  }

  if (explicit) {
    return explicit;
  }

  const api = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8005";
  return api.replace(/^http/, "ws").replace(/\/$/, "");
}
