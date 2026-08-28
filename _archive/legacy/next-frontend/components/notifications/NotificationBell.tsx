"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useNotifications } from "@/hooks/useNotifications";
import { useT } from "@/lib/i18n/context";
import type { Messages } from "@/lib/i18n/types";
import type { AppNotification } from "@/lib/types/api";
import styles from "./NotificationBell.module.css";

function notificationLabel(t: Messages, n: AppNotification): string {
  const kinds = t.notifications?.kind;
  return (kinds && kinds[n.kind]) || t.notifications?.title || "";
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function NotificationBell() {
  const t = useT();
  const {
    notifications,
    unreadCount,
    markRead,
    markAllRead,
    routeFor,
  } = useNotifications();

  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  const onNavigate = useCallback(
    (n: AppNotification) => {
      setOpen(false);
      void markRead(n.id);
    },
    [markRead],
  );

  useEffect(() => {
    if (!open) return;
    const onClick = (ev: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(ev.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className={styles.wrap} ref={rootRef}>
      <button
        type="button"
        className={styles.bell}
        aria-label={t.notifications.ariaOpen}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden="true" className={styles.icon}>
          🔔
        </span>
        {unreadCount > 0 ? (
          <span className={styles.badge} aria-label={`${unreadCount}`}>
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        ) : null}
      </button>

      {open ? (
        <div className={styles.dropdown} role="menu" aria-label={t.notifications.title}>
          <div className={styles.dropdownHead}>
            <span className={styles.dropdownTitle}>{t.notifications.title}</span>
            {unreadCount > 0 ? (
              <button
                type="button"
                className={styles.markAll}
                onClick={() => void markAllRead()}
              >
                {t.notifications.markAllRead}
              </button>
            ) : null}
          </div>
          {notifications.length === 0 ? (
            <p className={styles.empty}>{t.notifications.empty}</p>
          ) : (
            <ul className={styles.list}>
              {notifications.slice(0, 10).map((n) => {
                const href = routeFor(n);
                const read = n.is_read;
                return (
                  <li key={n.id} className={read ? styles.itemRead : styles.item}>
                    <Link
                      href={href}
                      className={styles.itemLink}
                      onClick={() => onNavigate(n)}
                    >
                      <span className={styles.itemText}>
                        {notificationLabel(t, n)}
                      </span>
                      <span className={styles.itemTime}>
                        {formatTime(n.created_at)}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
