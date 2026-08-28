"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { SupportCloud } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n/context";
import styles from "./AuthorClouds.module.css";

interface AuthorCloudsProps {
  storyId: string;
}

export function AuthorClouds({ storyId }: AuthorCloudsProps) {
  const { locale, t } = useI18n();
  const [clouds, setClouds] = useState<SupportCloud[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const list = await api.storyClouds(storyId);
      setClouds(list);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setClouds(null);
        setError(null);
        return;
      }
      setError(err instanceof ApiError ? err.message : t.common.error);
      setClouds([]);
    }
  }, [storyId, t.common.error]);

  useEffect(() => {
    if (open && clouds === null && !error) {
      void load();
    }
  }, [open, clouds, error, load]);

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.toggle}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {open ? t.clouds.hide : t.clouds.show}
      </button>
      {open ? (
        <div className={styles.panel}>
          {error ? <p className={styles.error}>{error}</p> : null}
          {clouds === null && !error ? (
            <p className={styles.meta}>{t.clouds.loading}</p>
          ) : null}
          {clouds && clouds.length === 0 ? (
            <p className={styles.meta}>{t.clouds.empty}</p>
          ) : null}
          {clouds && clouds.length > 0 ? (
            <ul className={styles.list}>
              {clouds.map((c) => (
                <li
                  key={c.id}
                  className={c.is_priority ? styles.cloudPriority : styles.cloud}
                >
                  {c.helper_badge ? (
                    <p className={styles.badge}>{c.helper_badge}</p>
                  ) : null}
                  <p className={styles.body}>{c.body}</p>
                  <p className={styles.meta}>
                    {c.pseudonym}
                    {c.kind === "free_text" ? ` · ${t.clouds.freeText}` : ""}
                    {c.created_at
                      ? ` · ${new Date(c.created_at).toLocaleString(
                          locale === "en" ? "en-GB" : "ru-RU",
                          {
                            day: "numeric",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          },
                        )}`
                      : null}
                  </p>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
