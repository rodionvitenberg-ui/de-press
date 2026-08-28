"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { TextArea } from "@/components/ui/TextArea";
import { useI18n } from "@/lib/i18n/context";
import styles from "./page.module.css";

interface Turn {
  role: "user" | "assistant";
  content: string;
  crisis?: boolean;
}

export default function CompanionPage() {
  const { t } = useI18n();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [disclaimer, setDisclaimer] = useState("");

  async function send() {
    const text = input.trim();
    if (!text) return;
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
    <div className={styles.page}>
      <h1 className={styles.title}>{t.companion.title}</h1>
      <div className={styles.banner}>
        {t.companion.bannerPrefix} <strong>{t.companion.bannerAi}</strong>
        {t.companion.bannerSuffix}{" "}
        <Link href="/anti-panic">{t.companion.bannerCrisis}</Link>, 112 / 103.
      </div>
      {offline ? <p className={styles.offline}>{t.companion.offline}</p> : null}

      <div className={styles.thread}>
        {turns.length === 0 ? (
          <p className={styles.offline}>{t.companion.empty}</p>
        ) : null}
        {turns.map((turn, i) => (
          <div
            key={`${turn.role}-${i}`}
            className={`${styles.msg} ${turn.role === "user" ? styles.user : styles.assistant} ${
              turn.crisis ? styles.crisis : ""
            }`}
          >
            {turn.content}
          </div>
        ))}
      </div>

      <div className={styles.compose}>
        <TextArea
          id="ai-input"
          label={t.companion.label}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          disabled={loading}
        />
        {error ? <p className={styles.error}>{error}</p> : null}
        <Button onClick={send} disabled={loading || !input.trim()}>
          {loading ? t.companion.sending : t.companion.send}
        </Button>
        {disclaimer ? <p className={styles.disclaimer}>{disclaimer}</p> : null}
      </div>
    </div>
  );
}