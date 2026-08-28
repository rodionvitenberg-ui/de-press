"use client";

import { useState } from "react";
import { useLocalMemory } from "@/hooks/useLocalMemory";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextArea";
import { useI18n } from "@/lib/i18n/context";
import styles from "./page.module.css";

export default function PatternsPage() {
  const { locale, t } = useI18n();
  const { ready, error, entries, meta, summary, add, toggleAnalytics, wipe } =
    useLocalMemory();
  const [level, setLevel] = useState(3);
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function onAdd() {
    setMsg(null);
    try {
      await add(level, note);
      setNote("");
      setMsg(t.patterns.saved);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : t.patterns.errorPrefix);
    }
  }

  if (!ready) {
    return <p className={styles.banner}>{t.patterns.loading}</p>;
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t.patterns.title}</h1>
      <p className={styles.banner}>{t.patterns.zkBanner}</p>
      {error ? <p className={styles.error}>{error}</p> : null}

      <section className={styles.card}>
        <p className={styles.stat}>
          {t.patterns.statsCount}: {summary.count}
          {summary.avgLevel != null
            ? ` · ${t.patterns.statsAvg} ${summary.avgLevel}/5`
            : ""}
          {` · ${t.patterns.statsLast7}: ${summary.last7}`}
          {` · ${t.patterns.statsTrend}: ${
            {
              up: t.patterns.trendUp,
              down: t.patterns.trendDown,
              flat: t.patterns.trendFlat,
              unknown: t.patterns.trendUnknown,
            }[summary.trend]
          }`}
        </p>
        <label>
          <input
            type="checkbox"
            checked={meta.analyticsEnabled}
            onChange={(e) => void toggleAnalytics(e.target.checked)}
          />{" "}
          {t.patterns.analyticsLabel}
        </label>
      </section>

      {meta.analyticsEnabled ? (
        <section className={styles.card}>
          <p>{t.patterns.howFeel}</p>
          <div className={styles.levels}>
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                className={n === level ? styles.active : ""}
                onClick={() => setLevel(n)}
              >
                {n}
              </button>
            ))}
          </div>
          <TextInput
            id="note"
            label={t.patterns.noteLabel}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t.patterns.notePlaceholder}
          />
          <Button onClick={() => void onAdd()}>{t.patterns.saveLocal}</Button>
          {msg ? <p className={styles.banner}>{msg}</p> : null}
        </section>
      ) : (
        <p className={styles.banner}>{t.patterns.disabled}</p>
      )}

      <section className={styles.card}>
        <h2>{t.patterns.recent}</h2>
        {entries.length === 0 ? (
          <p className={styles.banner}>{t.patterns.empty}</p>
        ) : (
          <div className={styles.list}>
            {entries.slice(0, 20).map((e) => (
              <div key={e.id} className={styles.row}>
                <span>
                  {e.level}/5 {e.note ? `— ${e.note}` : ""}
                </span>
                <span>
                  {new Date(e.at).toLocaleString(locale === "en" ? "en-GB" : "ru-RU")}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className={styles.actions}>
        <Button
          variant="danger"
          onClick={() => {
            if (window.confirm(t.patterns.wipeConfirm)) {
              void wipe();
            }
          }}
        >
          {t.patterns.wipe}
        </Button>
      </div>
    </div>
  );
}