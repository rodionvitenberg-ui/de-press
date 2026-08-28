import { useI18n } from "@/core/i18n/context";
import styles from "./CircleBubble.module.css";

interface CircleBubbleProps {
  videoUrl: string;
  durationMs?: number | null;
  fromMe: boolean;
}

/** Renders a Circle (ephemeral video note) in the dialogue thread. */
export function CircleBubble({ videoUrl, durationMs, fromMe }: CircleBubbleProps) {
  const { t } = useI18n();
  const sec =
    durationMs != null && durationMs > 0
      ? Math.max(1, Math.round(durationMs / 1000))
      : null;

  return (
    <div className={fromMe ? styles.wrapMe : styles.wrapThem}>
      <div className={styles.ring}>
        <video
          className={styles.video}
          src={videoUrl}
          controls
          playsInline
          preload="metadata"
        />
      </div>
      <div className={styles.meta}>
        <span className={styles.badge}>{t.chat.circleEphemeral}</span>
        {sec != null ? (
          <span className={styles.dur}>{sec}s</span>
        ) : null}
      </div>
    </div>
  );
}
