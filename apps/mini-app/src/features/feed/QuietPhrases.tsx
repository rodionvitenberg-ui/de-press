import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import styles from "./QuietPhrases.module.css";

interface QuietPhrasesProps {
  storyId: string;
}

/**
 * Quiet Phrases = one-tap private Support Cloud (not public comments).
 * Silent Empathy is separate («лучи»).
 */
export function QuietPhrases({ storyId }: QuietPhrasesProps) {
  const { locale, t } = useI18n();
  const [sentKeys, setSentKeys] = useState<Set<string>>(() => new Set());
  const [status, setStatus] = useState<string | null>(null);

  const phrasesQuery = useQuery({
    queryKey: ["quiet-phrases", locale],
    queryFn: () => api.quietPhrases(locale),
  });

  const send = useMutation({
    mutationFn: (key: string) => api.sendQuietPhrase(storyId, key),
    onSuccess: (res, key) => {
      setSentKeys((prev) => new Set(prev).add(key));
      setStatus(res.message || t.support.sentPhrase);
    },
    onError: (err) => {
      setStatus(err instanceof ApiError ? err.message : t.common.error);
    },
  });

  const phrases = phrasesQuery.data ?? [];

  return (
    <section className={styles.wrap} aria-labelledby="quiet-phrases-title">
      <h2 id="quiet-phrases-title" className={styles.title}>
        {t.support.title}
      </h2>
      <p className={styles.lead}>{t.support.lead}</p>

      {phrasesQuery.isError ? (
        <p className={styles.hint}>
          {phrasesQuery.error instanceof ApiError
            ? phrasesQuery.error.message
            : t.common.error}
        </p>
      ) : null}

      {phrases.length > 0 ? (
        <ul className={styles.list}>
          {phrases.map((p) => {
            const sent = sentKeys.has(p.key);
            const busy = send.isPending && send.variables === p.key;
            return (
              <li key={p.key}>
                <button
                  type="button"
                  className={sent ? styles.chipSent : styles.chip}
                  disabled={busy || sent}
                  onClick={() => {
                    setStatus(null);
                    send.mutate(p.key);
                  }}
                  aria-label={
                    sent ? `${t.support.sentPhrase}: ${p.text}` : p.text
                  }
                >
                  {p.text}
                </button>
              </li>
            );
          })}
        </ul>
      ) : phrasesQuery.isLoading ? (
        <p className={styles.hint}>{t.common.loading}</p>
      ) : null}

      {status ? (
        <p className={styles.hint} role="status" aria-live="polite">
          {status}
        </p>
      ) : null}
    </section>
  );
}
