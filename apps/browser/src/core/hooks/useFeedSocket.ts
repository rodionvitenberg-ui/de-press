import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { AuthorStory, Me, Story, StoryThread } from "@/core/api/types";
import { registerSocket } from "@/core/ws/registry";
import { buildWsBase } from "@/core/ws/url";
import {
  applyFeedEvent,
  isMine,
  type FeedEvent,
  type FeedInfinite,
} from "@/features/feed/applyFeedEvent";

export type FeedLiveStatus = "connecting" | "open" | "closed" | "error";

type ServerEnvelope = FeedEvent | { type: "pong" | "error"; detail?: string };

function buildWsUrl(): string {
  return `${buildWsBase()}/ws/feed/`;
}

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 15_000;
const RECONNECT_MAX_ATTEMPTS = 10;
const PING_MS = 25_000;

function isFeedEvent(data: ServerEnvelope): data is FeedEvent {
  return (
    data.type === "story.published" ||
    data.type === "story.updated" ||
    data.type === "story.hidden" ||
    data.type === "story.unhidden" ||
    data.type === "story.deleted" ||
    data.type === "story.commented"
  );
}

function patchThreads(
  queryClient: ReturnType<typeof useQueryClient>,
  event: FeedEvent,
) {
  queryClient.setQueriesData<StoryThread>(
    { queryKey: ["story-thread"] },
    (prev) => {
      if (!prev?.items) return prev;
      if (event.type === "story.deleted") {
        return {
          items: prev.items.filter((s) => s.id !== event.story_id),
        };
      }
      const story = event.story;
      if (event.type === "story.updated" || event.type === "story.hidden") {
        return {
          items: prev.items.map((s) =>
            s.id === story.id ? { ...s, ...story } : s,
          ),
        };
      }
      if (event.type === "story.commented") {
        const postId = event.post_id;
        if (!prev.items.some((s) => s.id === postId)) return prev;
        if (prev.items.some((s) => s.id === event.story.id)) return prev;
        return { items: [...prev.items, event.story] };
      }
      if (event.type === "story.published" || event.type === "story.unhidden") {
        if (event.story.parent_id) return prev;
        if (prev.items.some((s) => s.id === story.id)) {
          return {
            items: prev.items.map((s) =>
              s.id === story.id ? { ...s, ...story } : s,
            ),
          };
        }
        return prev;
      }
      return prev;
    },
  );
}

function patchMine(
  queryClient: ReturnType<typeof useQueryClient>,
  event: FeedEvent,
  me: Me | null | undefined,
) {
  queryClient.setQueryData<AuthorStory[]>(["my-stories"], (prev) => {
    if (!prev) return prev;
    if (event.type === "story.deleted") {
      return prev.filter((s) => s.id !== event.story_id);
    }
    const story = event.story;
    if (!isMine(story, me)) return prev;
    if (event.type === "story.updated" || event.type === "story.hidden") {
      return prev.map((s) => (s.id === story.id ? { ...s, ...story } : s));
    }
    if (event.type === "story.commented") {
      const postId = event.post_id;
      const post = prev.find((s) => s.id === postId);
      if (!post) return prev;
      return [post, ...prev.filter((s) => s.id !== postId)];
    }
    if (event.type === "story.published" || event.type === "story.unhidden") {
      if (story.parent_id) return prev;
      const rest = prev.filter((s) => s.id !== story.id);
      return [{ ...story, pulse_count: 0, pulse_message: "" }, ...rest];
    }
    return prev;
  });
}

/**
 * Live public feed: WS primary while /feed is mounted. HTTP poll is the fallback.
 */
export function useFeedSocket(enabled = true) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<FeedLiveStatus>("closed");
  const wsRef = useRef<WebSocket | null>(null);
  const intentionalClose = useRef(false);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const attemptRef = useRef(0);
  const enabledRef = useRef(enabled);

  enabledRef.current = enabled;

  useEffect(() => {
    if (!enabled) {
      setStatus("closed");
      return;
    }

    intentionalClose.current = false;
    let cancelled = false;

    const clearPing = () => {
      if (pingTimer.current) {
        clearInterval(pingTimer.current);
        pingTimer.current = null;
      }
    };

    const applyEvent = (event: FeedEvent) => {
      const me = queryClient.getQueryData<Me>(["me"]);
      queryClient.setQueryData<FeedInfinite>(["feed"], (prev) =>
        applyFeedEvent(prev, event, me),
      );
      patchMine(queryClient, event, me);
      patchThreads(queryClient, event);
      if (event.type === "story.deleted") {
        queryClient.removeQueries({ queryKey: ["story", event.story_id] });
        return;
      }
      const story: Story = event.story;
      queryClient.setQueryData<Story>(["story", story.id], (prev) =>
        prev ? { ...prev, ...story } : story,
      );
    };

    const handleEnvelope = (data: ServerEnvelope) => {
      if (data.type === "pong" || data.type === "error") return;
      if (isFeedEvent(data)) applyEvent(data);
    };

    const connect = () => {
      if (cancelled || intentionalClose.current || !enabledRef.current) return;
      setStatus("connecting");
      const ws = new WebSocket(buildWsUrl());
      wsRef.current = ws;
      registerSocket(ws);

      ws.onopen = () => {
        if (cancelled) return;
        setStatus("open");
        attemptRef.current = 0;
        void queryClient.invalidateQueries({ queryKey: ["feed"] });
        clearPing();
        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, PING_MS);
      };

      ws.onmessage = (ev) => {
        try {
          handleEnvelope(JSON.parse(ev.data as string) as ServerEnvelope);
        } catch {
          /* ignore malformed */
        }
      };

      ws.onerror = () => {
        /* onclose schedules reconnect */
      };

      ws.onclose = () => {
        clearPing();
        if (cancelled) return;
        wsRef.current = null;
        if (intentionalClose.current) {
          setStatus("closed");
          return;
        }
        const attempt = attemptRef.current;
        if (attempt >= RECONNECT_MAX_ATTEMPTS) {
          setStatus("error");
          return;
        }
        setStatus("connecting");
        const delay = Math.min(
          RECONNECT_BASE_MS * 2 ** attempt,
          RECONNECT_MAX_MS,
        );
        attemptRef.current = attempt + 1;
        reconnectTimer.current = setTimeout(() => {
          connect();
        }, delay);
      };
    };

    connect();

    return () => {
      cancelled = true;
      intentionalClose.current = true;
      clearPing();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [enabled, queryClient]);

  return { status };
}
