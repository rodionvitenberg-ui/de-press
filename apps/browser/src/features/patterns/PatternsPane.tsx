import { useState } from "react";
import { useLocalMemory } from "@/core/hooks/useLocalMemory";
import { useI18n } from "@/core/i18n/context";
import { useToast } from "@/core/toast";
import styles from "./PatternsPane.module.css";

export function PatternsPane() {
  const { locale, t } = useI18n();
  const toast = useToast();
  const { ready, error, entries, meta, summary, add, toggleAnalytics, wipe } =
    useLocalMemory();
  const [level, setLevel] = useState(3);
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onAdd() {
    setMsg(null);
    setSaving(true);
    try {
      await add(level, note);
      setNote("");
      setMsg(t.patterns.saved);
    } catch (err) {
      setMsg(
        err instanceof Error
          ? `${t.patterns.errorPrefix}: ${err.message}`
          : t.patterns.errorPrefix,
      );
    } finally {
      setSaving(false);
    }
  }

  if (!ready) {
    return (
      <div className={styles.pane}>
        <p className={styles.muted}>{t.patterns.loading}</p>
      </div>
    );
  }

  const trendLabel = {
    up: t.patterns.trendUp,
    down: t.patterns.trendDown,
    flat: t.patterns.trendFlat,
    unknown: t.patterns.trendUnknown,
  }[summary.trend];

  return (
    <div className={styles.pane}>
      <header className={styles.head}>
        <h1 className={styles.title}>{t.patterns.title}</h1>
        <p className={styles.banner}>{t.patterns.zkBanner}</p>
      </header>

      {error ? <p className={styles.error}>{error}</p> : null}

      <section className={styles.card}>
        <p className={styles.stat}>
          {t.patterns.statsCount}: {summary.count}
          {summary.avgLevel != null
            ? ` · ${t.patterns.statsAvg} ${summary.avgLevel}/5`
            : ""}
          {` · ${t.patterns.statsLast7}: ${summary.last7}`}
          {` · ${t.patterns.statsTrend}: ${trendLabel}`}
        </p>
        <label className={styles.check}>
          <input
            type="checkbox"
            checked={meta.analyticsEnabled}
            onChange={(e) => void toggleAnalytics(e.target.checked)}
          />
          <span>{t.patterns.analyticsLabel}</span>
        </label>
      </section>

      {meta.analyticsEnabled ? (
        <section className={styles.card}>
          <p className={styles.howFeel}>{t.patterns.howFeel}</p>
          <div className={styles.levels} role="group" aria-label={t.patterns.howFeel}>
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                className={n === level ? styles.levelActive : styles.level}
                onClick={() => setLevel(n)}
                aria-pressed={n === level}
              >
                {n}
              </button>
            ))}
          </div>
          <label className={styles.field}>
            <span>{t.patterns.noteLabel}</span>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={t.patterns.notePlaceholder}
              maxLength={500}
            />
          </label>
          <button
            type="button"
            className={styles.primary}
            disabled={saving}
            onClick={() => void onAdd()}
          >
            {t.patterns.saveLocal}
          </button>
          {msg ? (
            <p className={styles.muted} role="status">
              {msg}
            </p>
          ) : null}
        </section>
      ) : (
        <p className={styles.muted}>{t.patterns.disabled}</p>
      )}

      <section className={styles.card}>
        <h2 className={styles.sectionTitle}>{t.patterns.recent}</h2>
        {entries.length === 0 ? (
          <p className={styles.muted}>{t.patterns.empty}</p>
        ) : (
          <ul className={styles.list}>
            {entries.slice(0, 20).map((e) => (
              <li key={e.id} className={styles.row}>
                <span className={styles.rowMain}>
                  <strong>{e.level}/5</strong>
                  {e.note ? ` — ${e.note}` : ""}
                </span>
                <time className={styles.rowTime}>
                  {new Date(e.at).toLocaleString(
                    locale === "en" ? "en-GB" : "ru-RU",
                  )}
                </time>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.danger}
          onClick={() => {
            void (async () => {
              const ok = await toast.confirm({
                message: t.patterns.wipeConfirm,
                confirmLabel: t.chat.confirmYes,
                cancelLabel: t.chat.confirmNo,
                danger: true,
              });
              if (ok) void wipe();
            })();
          }}
        >
          {t.patterns.wipe}
        </button>
      </div>
    </div>
  );
}
