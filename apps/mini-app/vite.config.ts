import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// API и WebSocket проксируются на Django (daphne :8005).
// Единый origin: app.depress.co (dev: http://localhost:5174).
const API_UPSTREAM = process.env.API_UPSTREAM ?? "http://127.0.0.1:8005";

export default defineConfig(({ command }) => ({
  // Прод: mini-app раздаётся nginx-ом по пути /tg/ (deploy/nginx-de-press.conf).
  // В dev base не меняем — дев-сервер остаётся на /.
  base: command === "build" ? "/tg/" : "/",
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5175,
    // 0.0.0.0 so tunnels (ngrok/cloudflared) can reach Mini App dev
    host: "0.0.0.0",
    proxy: {
      "/api": { target: API_UPSTREAM, changeOrigin: true },
      "/media": { target: API_UPSTREAM, changeOrigin: true },
      "/docs": { target: API_UPSTREAM, changeOrigin: true },
      "/openapi.json": { target: API_UPSTREAM, changeOrigin: true },
      "/ws": {
        target: API_UPSTREAM.replace(/^http/, "ws"),
        ws: true,
      },
    },
    headers: {
      // Mini App may open in TG WebView/iframe-like contexts
      "Content-Security-Policy":
        "frame-ancestors 'self' https://web.telegram.org https://telegram.org https://*.telegram.org;",
    },
  },
}));