"use client";

import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { useI18n } from "@/lib/i18n/context";
import styles from "./BreathingCanvas.module.css";

type Branch = "menu" | "breathe" | "ground" | "vent" | "speak" | "ai";

export function BreathingCanvas() {
  const { t } = useI18n();

  const PHASES = useMemo(
    () => [
      { label: t.antiPanic.breatheInhale, durationMs: 4000 },
      { label: t.antiPanic.breatheHold, durationMs: 7000 },
      { label: t.antiPanic.breatheExhale, durationMs: 8000 },
    ],
    [t],
  );

  const [branch, setBranch] = useState<Branch>("menu");
  const [index, setIndex] = useState(0);
  const [vent, setVent] = useState("");
  const [aiInput, setAiInput] = useState("");
  const [aiReply, setAiReply] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  useEffect(() => {
    if (branch !== "breathe") return;
    const timer = window.setTimeout(() => {
      setIndex((i) => (i + 1) % PHASES.length);
    }, PHASES[index].durationMs);
    return () => window.clearTimeout(timer);
  }, [index, branch, PHASES]);

  async function askAi() {
    const text = aiInput.trim();
    if (!text) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const res = await api.aiSupport(
        [{ role: "user", content: text }],
        "anti_panic",
      );
      setAiReply(res.reply);
    } catch (err) {
      setAiError(err instanceof ApiError ? err.message : t.antiPanic.aiError);
    } finally {
      setAiLoading(false);
    }
  }

  if (branch === "menu") {
    return (
      <div className={styles.canvas}>
        <p className={styles.phase}>{t.antiPanic.menuTitle}</p>
        <p className={styles.hint}>{t.antiPanic.menuHint}</p>
        <ul className={styles.menu}>
          <li>
            <button type="button" onClick={() => setBranch("breathe")}>
              {t.antiPanic.menuBreathe}
            </button>
          </li>
          <li>
            <button type="button" onClick={() => setBranch("ground")}>
              {t.antiPanic.menuGround}
            </button>
          </li>
          <li>
            <button type="button" onClick={() => setBranch("vent")}>
              {t.antiPanic.menuVent}
            </button>
          </li>
          <li>
            <button type="button" onClick={() => setBranch("speak")}>
              {t.antiPanic.menuSpeak}
            </button>
          </li>
          <li>
            <button type="button" onClick={() => setBranch("ai")}>
              {t.antiPanic.menuAi}
            </button>
          </li>
        </ul>
      </div>
    );
  }

  if (branch === "ground") {
    return (
      <div className={styles.canvas}>
        <p className={styles.phase}>{t.antiPanic.groundTitle}</p>
        <ul className={styles.steps}>
          {t.antiPanic.groundSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
        <button
          type="button"
          className={styles.back}
          onClick={() => setBranch("menu")}
        >
          {t.antiPanic.back}
        </button>
      </div>
    );
  }

  if (branch === "ai") {
    return (
      <div className={styles.canvas}>
        <p className={styles.phase}>{t.antiPanic.aiTitle}</p>
        <p className={styles.hint}>{t.antiPanic.aiHint}</p>
        <textarea
          className={styles.vent}
          value={aiInput}
          onChange={(e) => setAiInput(e.target.value)}
          rows={4}
          placeholder={t.antiPanic.aiPlaceholder}
        />
        <button
          type="button"
          className={styles.menuBtn}
          onClick={() => void askAi()}
          disabled={aiLoading}
        >
          {aiLoading ? t.antiPanic.aiLoading : t.antiPanic.aiAsk}
        </button>
        {aiError ? <p className={styles.hint}>{aiError}</p> : null}
        {aiReply ? <p className={styles.hint}>{aiReply}</p> : null}
        <button
          type="button"
          className={styles.back}
          onClick={() => setBranch("menu")}
        >
          {t.antiPanic.back}
        </button>
      </div>
    );
  }

  if (branch === "vent" || branch === "speak") {
    return (
      <div className={styles.canvas}>
        <p className={styles.phase}>
          {branch === "vent" ? t.antiPanic.ventTitle : t.antiPanic.speakTitle}
        </p>
        <p className={styles.hint}>{t.antiPanic.ventHint}</p>
        <textarea
          className={styles.vent}
          value={vent}
          onChange={(e) => setVent(e.target.value)}
          rows={8}
          placeholder={t.antiPanic.ventPlaceholder}
        />
        <button
          type="button"
          className={styles.back}
          onClick={() => {
            setVent("");
            setBranch("menu");
          }}
        >
          {t.antiPanic.eraseBack}
        </button>
      </div>
    );
  }

  return (
    <div className={styles.canvas}>
      <div className={styles.circle} aria-hidden />
      <p className={styles.phase}>{PHASES[index].label}</p>
      <p className={styles.hint}>{t.antiPanic.breatheHint}</p>
      <button
        type="button"
        className={styles.back}
        onClick={() => setBranch("menu")}
      >
        {t.antiPanic.back}
      </button>
    </div>
  );
}