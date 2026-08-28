import { useEffect, useRef } from "react";
import { useI18n } from "@/core/i18n/context";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import styles from "./AntiPanicOverlay.module.css";

/**
 * Quiet-mode canvas: 4–7–8 + 5–4–3–2–1. Exit is explicit only (no Escape).
 */
export function AntiPanicOverlay() {
  const { active, exit } = useAntiPanic();
  const { t } = useI18n();
  const exitRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!active) return;
    exitRef.current?.focus();
  }, [active]);

  if (!active) return null;

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-label={t.antiPanic.menuTitle}
    >
      <div className={styles.panel}>
        <p className={styles.title}>{t.antiPanic.menuTitle}</p>
        <p className={styles.hint}>{t.antiPanic.breatheHint}</p>
        <div className={styles.breath} aria-hidden>
          <span className={styles.circle} />
        </div>
        <ol className={styles.steps}>
          {t.antiPanic.groundSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
        <button
          ref={exitRef}
          type="button"
          className={styles.exit}
          onClick={exit}
        >
          {t.nav.exitPanic}
        </button>
      </div>
    </div>
  );
}
