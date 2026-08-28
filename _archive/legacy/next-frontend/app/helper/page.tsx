"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { Me, QueueCloud } from "@/lib/types/api";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { HelperDashboard } from "@/components/moderation/HelperDashboard";
import styles from "./page.module.css";

export default function HelperQueuePage() {
  const t = useT();
  const [me, setMe] = useState<Me | null>(null);
  const [items, setItems] = useState<QueueCloud[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = await api.me();
      setMe(profile);
      if (!profile.is_helper && !profile.is_authenticated) {
        setItems([]);
        return;
      }
      const queue = await api.moderationQueue();
      setItems(queue);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError(t.helper.needRole);
        setItems([]);
      } else {
        setError(err instanceof ApiError ? err.message : t.common.error);
      }
    } finally {
      setLoading(false);
    }
  }, [t.common.error, t.helper.needRole]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onApprove(id: string) {
    setBusyId(id);
    setHint(null);
    try {
      const res = await api.approveCloud(id);
      setHint(res.message);
      setItems((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setBusyId(null);
    }
  }

  async function onReject(id: string) {
    setBusyId(id);
    setHint(null);
    try {
      const res = await api.rejectCloud(id);
      setHint(res.message);
      setItems((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setBusyId(null);
    }
  }

  const canModerate = Boolean(me?.is_helper || me?.is_authenticated);

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t.helper.title}</h1>
      <p className={styles.lead}>
        {t.helper.lead}{" "}
        <Link href="/help">/help</Link> · 112/103.
      </p>

      {me?.is_helper ? (
        <p className={styles.badge}>
          {me.helper_badge || "Helper"}
          {me.helper_org ? ` · ${me.helper_org}` : ""}
        </p>
      ) : (
        <p className={styles.meta}>{t.helper.needRole}</p>
      )}

      {me?.is_helper ? <HelperDashboard /> : null}

      {loading ? <p className={styles.meta}>{t.helper.loading}</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
      {hint ? <p className={styles.hint}>{hint}</p> : null}

      {!loading && canModerate && items.length === 0 && !error ? (
        <p className={styles.meta}>{t.helper.empty}</p>
      ) : null}

      <ul className={styles.list}>
        {items.map((c) => (
          <li key={c.id} className={styles.card}>
            <p className={styles.meta}>
              {t.helper.from} {c.pseudonym} ·{" "}
              <Link href={`/stories/${c.story_id}`}>{t.helper.toStory}</Link>
            </p>
            <p className={styles.preview}>{c.story_preview}…</p>
            <p className={styles.body}>{c.body}</p>
            <div className={styles.actions}>
              <Button
                disabled={busyId === c.id}
                onClick={() => onApprove(c.id)}
              >
                {t.helper.approve}
              </Button>
              <Button
                variant="ghost"
                disabled={busyId === c.id}
                onClick={() => onReject(c.id)}
              >
                {t.helper.reject}
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
