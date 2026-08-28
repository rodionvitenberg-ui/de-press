import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "@/core/api/client";
import type { AppNotification, NotificationKind } from "@/core/api/types";
import { useI18n } from "@/core/i18n/context";
import styles from "./NotificationsPane.module.css";

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const mins = Math.floor((Date.now() - then) / 60_000);
  if (mins < 1) return "·";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

function resolveTarget(n: AppNotification): string | null {
  const p = n.payload ?? {};
  if (p.dialogue_id) return `/chat/${p.dialogue_id}`;
  if (p.story_id) return `/feed/${p.story_id}`;
  if (n.kind === "dialogue_request") return "/chat";
  if (n.kind === "message" || n.kind === "dialogue_opened") return "/chat";
  return null;
}

export function NotificationsPane() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.notifications(40),
  });

  const markAll = useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
      await queryClient.invalidateQueries({
        queryKey: ["notifications-unread"],
      });
    },
  });

  const markOne = useMutation({
    mutationFn: (id: string) => api.markNotificationRead(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
      await queryClient.invalidateQueries({
        queryKey: ["notifications-unread"],
      });
    },
  });

  const items = listQuery.data ?? [];
  const unread = items.filter((n) => !n.is_read).length;

  async function openItem(n: AppNotification) {
    if (!n.is_read) {
      try {
        await markOne.mutateAsync(n.id);
      } catch {
        /* still navigate */
      }
    }
    const target = resolveTarget(n);
    if (target) navigate(target);
  }

  function kindLabel(kind: NotificationKind): string {
    return t.notifications.kind[kind] ?? kind;
  }

  return (
    <div className={styles.pane}>
      <header className={styles.head}>
        <h1 className={styles.title}>{t.notifications.title}</h1>
        {unread > 0 ? (
          <button
            type="button"
            className={styles.markAll}
            disabled={markAll.isPending}
            onClick={() => markAll.mutate()}
          >
            {t.notifications.markAllRead}
          </button>
        ) : null}
      </header>

      {listQuery.isLoading ? (
        <p className={styles.empty}>{t.common.loading}</p>
      ) : listQuery.isError ? (
        <p className={styles.empty}>
          {listQuery.error instanceof ApiError
            ? listQuery.error.message
            : t.common.error}
        </p>
      ) : items.length === 0 ? (
        <p className={styles.empty}>{t.notifications.empty}</p>
      ) : (
        <ul className={styles.list}>
          {items.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                className={
                  n.is_read
                    ? styles.row
                    : `${styles.row} ${styles.rowUnread}`
                }
                onClick={() => void openItem(n)}
              >
                <span
                  className={
                    n.is_read ? styles.dot : `${styles.dot} ${styles.dotOn}`
                  }
                  aria-hidden
                />
                <span className={styles.body}>
                  <span className={styles.kind}>{kindLabel(n.kind)}</span>
                  <time className={styles.time}>{timeAgo(n.created_at)}</time>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
