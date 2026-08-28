import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/core/api/client";
import type { AppNotification } from "@/core/api/types";
import { registerSocket } from "@/core/ws/registry";
import { buildWsBase } from "@/core/ws/url";

export type NotificationsStatus = "connecting" | "open" | "closed" | "error";

interface ServerEnvelope {
  type: string;
  notification?: AppNotification;
  notifications?: AppNotification[];
  unread_count?: number;
  detail?: string;
}

function buildWsUrl(): string {
  return `${buildWsBase()}/ws/notifications/`;
}

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 15_000;
const RECONNECT_MAX_ATTEMPTS = 10;
const POLL_INTERVAL_MS = 45_000;

/**
 * Live notifications: WS primary, HTTP poll fallback.
 * Syncs React Query keys used by Sidebar badges and NotificationsPane.
 */
export function useNotifications(
  enabled = true,
  onNew?: (n: AppNotification) => void,
) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<NotificationsStatus>("closed");
  const [error, setError] = useState<string | null>(null);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const intentionalClose = useRef(false);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const attemptRef = useRef(0);
  const enabledRef = useRef(enabled);
  const onNewRef = useRef(onNew);

  enabledRef.current = enabled;
  onNewRef.current = onNew;

  const syncQuery = useCallback(
    (patch?: {
      notifications?: AppNotification[];
      unread?: number;
      prepend?: AppNotification;
    }) => {
      if (patch?.notifications) {
        queryClient.setQueryData(["notifications"], patch.notifications);
      }
      if (patch?.prepend) {
        const n = patch.prepend;
        queryClient.setQueryData<AppNotification[]>(
          ["notifications"],
          (prev) => {
            const list = prev ?? [];
            if (list.some((x) => x.id === n.id)) return list;
            return [n, ...list].slice(0, 100);
          },
        );
      }
      if (typeof patch?.unread === "number") {
        queryClient.setQueryData(["notifications-unread"], {
          count: patch.unread,
        });
      }
    },
    [queryClient],
  );

  const loadViaHttp = useCallback(async () => {
    try {
      const [rows, count] = await Promise.all([
        api.notifications(40),
        api.notificationsUnreadCount(),
      ]);
      syncQuery({ notifications: rows, unread: count.count });
      setError(null);
    } catch {
      /* silent — WS is primary */
    }
  }, [syncQuery]);

  useEffect(() => {
    if (!enabled) return;
    void loadViaHttp();
    pollTimer.current = setInterval(() => {
      void loadViaHttp();
    }, POLL_INTERVAL_MS);
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, [enabled, loadViaHttp]);

  useEffect(() => {
    if (!enabled) return;

    intentionalClose.current = false;
    let cancelled = false;

    const handleEnvelope = (data: ServerEnvelope) => {
      if (data.type === "snapshot") {
        syncQuery({
          notifications: data.notifications,
          unread:
            typeof data.unread_count === "number"
              ? data.unread_count
              : undefined,
        });
      } else if (data.type === "notification.new" && data.notification) {
        const hide =
          data.notification.kind === "support_cloud" ||
          data.notification.kind === "cloud_approved" ||
          data.notification.kind === "silent_empathy";
        if (!hide) {
          syncQuery({ prepend: data.notification });
        }
        void queryClient.invalidateQueries({
          queryKey: ["notifications-unread"],
        });
        const kind = data.notification.kind;
        if (
          kind === "dialogue_request" ||
          kind === "dialogue_opened" ||
          kind === "outreach_intro" ||
          kind === "message" ||
          kind === "dialogue_deleted"
        ) {
          void queryClient.invalidateQueries({ queryKey: ["dialogues"] });
          void queryClient.invalidateQueries({
            queryKey: ["dialogue-requests"],
          });
        }
        if (
          kind === "support_cloud" ||
          kind === "cloud_approved" ||
          kind === "silent_empathy"
        ) {
          void queryClient.invalidateQueries({ queryKey: ["story"] });
          void queryClient.invalidateQueries({ queryKey: ["feed"] });
          void queryClient.invalidateQueries({ queryKey: ["my-stories"] });
          void queryClient.invalidateQueries({ queryKey: ["hearers"] });
        }
        if (
          kind !== "support_cloud" &&
          kind !== "cloud_approved" &&
          kind !== "silent_empathy"
        ) {
          onNewRef.current?.(data.notification);
        }
      } else if (data.type === "unread_count") {
        if (typeof data.unread_count === "number") {
          syncQuery({ unread: data.unread_count });
        }
      } else if (data.type === "error") {
        setError(data.detail || "Notification WS error");
      }
    };

    const connect = () => {
      if (cancelled || intentionalClose.current || !enabledRef.current) return;
      setStatus("connecting");
      setError(null);

      const ws = new WebSocket(buildWsUrl());
      wsRef.current = ws;
      registerSocket(ws);

      ws.onopen = () => {
        if (cancelled) return;
        setStatus("open");
        attemptRef.current = 0;
        setReconnectAttempt(0);
        setError(null);
      };

      ws.onmessage = (ev) => {
        try {
          handleEnvelope(JSON.parse(ev.data as string) as ServerEnvelope);
        } catch {
          setError("Bad notification WS payload");
        }
      };

      ws.onerror = () => {
        /* onclose schedules reconnect */
      };

      ws.onclose = () => {
        if (cancelled) return;
        wsRef.current = null;
        if (intentionalClose.current) {
          setStatus("closed");
          return;
        }

        const attempt = attemptRef.current;
        if (attempt >= RECONNECT_MAX_ATTEMPTS) {
          setStatus("error");
          setError("Notifications WS unavailable");
          return;
        }

        setStatus("connecting");
        const delay = Math.min(
          RECONNECT_BASE_MS * 2 ** attempt,
          RECONNECT_MAX_MS,
        );
        attemptRef.current = attempt + 1;
        setReconnectAttempt(attempt + 1);
        reconnectTimer.current = setTimeout(() => {
          connect();
        }, delay);
      };
    };

    connect();

    return () => {
      cancelled = true;
      intentionalClose.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [enabled, queryClient, syncQuery]);

  return {
    status,
    error,
    reconnectAttempt,
    refresh: loadViaHttp,
  };
}
