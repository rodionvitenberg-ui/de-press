import { useState } from "react";
import { api, ApiError } from "@/core/api/client";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useI18n } from "@/core/i18n/context";
import styles from "./CompanionPane.module.css";

type Turn = { role: "user" | "assistant"; content: string; crisis?: boolean };

/**
 * Quiet Companion: session-only AI chat via api.aiSupport(..., "companion").
 * Not IndexedDB, not the chat list. Crisis replies open Anti-Panic.
 */
export function CompanionPane() {
  const { t } = useI18n();
  const { enter } = useAntiPanic();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [disclaimer, setDisclaimer] = useState("");

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setLoading(true);
    setError(null);
    const nextUser: Turn = { role: "user", content: text };
    const history = [...turns, nextUser];
    setTurns(history);
    setInput("");
    try {
      const res = await api.aiSupport(
        history.map((turn) => ({ role: turn.role, content: turn.content })),
        "companion",
      );
      setOffline(res.offline);
      setDisclaimer(res.disclaimer);
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: res.reply, crisis: res.crisis },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.companion.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.pane}>
      <header className={styles.head}>
        <h1 className={styles.title}>{t.companion.title}</h1>
        <p className={styles.banner}>
          {t.companion.bannerPrefix}{" "}
          <strong>{t.companion.bannerAi}</strong>
          {t.companion.bannerSuffix}{" "}
          <button type="button" className={styles.bannerLink} onClick={enter}>
            {t.companion.bannerCrisis}
          </button>
          , 112 / 103.
        </p>
        {offline ? <p className={styles.offline}>{t.companion.offline}</p> : null}
      </header>

      <div className={styles.thread} aria-live="polite">
        {turns.length === 0 ? (
          <p className={styles.empty}>{t.companion.empty}</p>
        ) : null}
        {turns.map((turn, i) => (
          <div
            key={`${turn.role}-${i}`}
            className={[
              styles.msg,
              turn.role === "user" ? styles.user : styles.assistant,
              turn.crisis ? styles.crisis : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <p className={styles.msgBody}>{turn.content}</p>
            {turn.crisis ? (
              <button
                type="button"
                className={styles.crisisBtn}
                onClick={enter}
              >
                {t.companion.bannerCrisis}
              </button>
            ) : null}
          </div>
        ))}
      </div>

      <div className={styles.compose}>
        <label className={styles.label} htmlFor="companion-input">
          {t.companion.label}
        </label>
        <textarea
          id="companion-input"
          className={styles.input}
          rows={3}
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}
        <button
          type="button"
          className={styles.send}
          disabled={loading || !input.trim()}
          onClick={() => void send()}
        >
          {loading ? t.companion.sending : t.companion.send}
        </button>
        {disclaimer ? (
          <p className={styles.disclaimer}>{disclaimer}</p>
        ) : null}
      </div>
    </div>
  );
}
