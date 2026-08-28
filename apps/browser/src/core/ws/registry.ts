/**
 * Global registry of open WebSockets so Anti-Panic can kill realtime.
 */

const sockets = new Set<WebSocket>();

export function registerSocket(ws: WebSocket): void {
  sockets.add(ws);
  const cleanup = () => sockets.delete(ws);
  ws.addEventListener("close", cleanup);
  ws.addEventListener("error", cleanup);
}

export function killAllSockets(): void {
  for (const ws of sockets) {
    try {
      ws.close(4000, "anti-panic");
    } catch {
      /* ignore */
    }
  }
  sockets.clear();
}

export function activeSocketCount(): number {
  return sockets.size;
}
