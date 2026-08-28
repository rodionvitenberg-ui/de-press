"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { QuietPhrase } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n/context";
import { ModeratedCloudForm } from "@/components/support/ModeratedCloudForm";
import styles from "./QuietPhrases.module.css";

interface QuietPhrasesProps {
  storyId: string;
}

export function QuietPhrases({ storyId }: QuietPhrasesProps) {
  const { locale, t } = useI18n();
  const [phrases, setPhrases] = useState<QuietPhrase[]>([]);
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [sentKeys, setSentKeys] = useState<Set<string>>(new Set());
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await api.quietPhrases(locale);
        if (!cancelled) {
          setPhrases(list);
          setLoadError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError ? err.message : t.common.error,
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [locale, t.common.error]);

  async function onSend(key: string) {
    setLoadingKey(key);
    setMessage(null);
    try {
      const res = await api.sendQuietPhrase(storyId, key);
      setMessage(res.message);
      setSentKeys((prev) => new Set(prev).add(key));
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setLoadingKey(null);
    }
  }

  return (
    <div className={styles.wrap}>
      <h2 className={styles.title}>{t.support.title}</h2>
      <p className={styles.lead}>{t.support.lead}</p>
      {loadError ? <p className={styles.hint}>{loadError}</p> : null}
      {phrases.length > 0 ? (
        <ul className={styles.list}>
          {phrases.map((p) => {
            const sent = sentKeys.has(p.key);
            const busy = loadingKey === p.key;
            return (
              <li key={p.key}>
                <button
                  type="button"
                  className={sent ? styles.chipSent : styles.chip}
                  onClick={() => onSend(p.key)}
                  disabled={busy || sent}
                  aria-label={
                    sent
                      ? `${t.support.sentPhrase}: ${p.text}`
                      : p.text
                  }
                >
                  {p.text}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
      {message ? <p className={styles.hint}>{message}</p> : null}
      <ModeratedCloudForm storyId={storyId} />
    </div>
  );
}
