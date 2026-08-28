import styles from "./EmotionSticker.module.css";

export const GESTURE_KEYS = ["i_am_here", "i_hear", "not_alone"] as const;
export type GestureKey = (typeof GESTURE_KEYS)[number];

export function isGestureKey(key: string): key is GestureKey {
  return (GESTURE_KEYS as readonly string[]).includes(key);
}

interface EmotionStickerProps {
  gesture: GestureKey;
  label: string;
  caption?: string;
  asButton?: boolean;
  disabled?: boolean;
  sent?: boolean;
  compact?: boolean;
  mini?: boolean;
  onClick?: () => void;
}

export function EmotionSticker({
  gesture,
  label,
  caption,
  asButton = false,
  disabled,
  sent,
  compact,
  mini,
  onClick,
}: EmotionStickerProps) {
  const className = [
    styles.sticker,
    sent ? styles.stickerSent : "",
    compact ? styles.stickerCompact : "",
    mini ? styles.stickerMini : "",
  ]
    .filter(Boolean)
    .join(" ");

  const inner = (
    <>
      <span className={styles.stage} aria-hidden>
        {gesture === "i_am_here" ? <HereArt /> : null}
        {gesture === "i_hear" ? <HearArt /> : null}
        {gesture === "not_alone" ? <TogetherArt /> : null}
      </span>
      {caption ? <span className={styles.caption}>{caption}</span> : null}
      <span className={styles.srOnly}>{label}</span>
    </>
  );

  if (!asButton) {
    return (
      <span className={className} title={label}>
        {inner}
      </span>
    );
  }

  return (
    <button
      type="button"
      className={className}
      disabled={disabled}
      onClick={onClick}
      aria-label={label}
      title={label}
    >
      {inner}
    </button>
  );
}

function HereArt() {
  return (
    <svg viewBox="0 0 64 64" className={`${styles.art} ${styles.here}`}>
      <ellipse className={styles.ground} cx="32" cy="50" rx="14" ry="3.2" />
      <g className={styles.figure}>
        <rect className={styles.body} x="24" y="28" width="16" height="18" rx="8" />
        <circle className={styles.head} cx="32" cy="22" r="8" />
        <circle className={styles.shine} cx="29" cy="19" r="2.2" />
      </g>
    </svg>
  );
}

function HearArt() {
  return (
    <svg viewBox="0 0 64 64" className={`${styles.art} ${styles.hear}`}>
      <ellipse className={styles.ground} cx="32" cy="50" rx="13" ry="3" />
      <g className={styles.heart}>
        <path
          className={styles.heartShape}
          d="M32 46C32 46 12 33 12 22.5 12 15.5 17.2 12 22.8 12 26.4 12 29.4 13.8 32 17.2 34.6 13.8 37.6 12 41.2 12 46.8 12 52 15.5 52 22.5 52 33 32 46 32 46Z"
        />
        <circle className={styles.shine} cx="24.5" cy="20" r="2.4" />
      </g>
    </svg>
  );
}

function TogetherArt() {
  return (
    <svg viewBox="0 0 64 64" className={`${styles.art} ${styles.together}`}>
      <ellipse className={styles.ground} cx="32" cy="50" rx="18" ry="3.2" />
      <g className={styles.left}>
        <rect className={styles.body} x="12" y="30" width="14" height="16" rx="7" />
        <circle className={styles.head} cx="19" cy="24" r="7" />
        <circle className={styles.shine} cx="16.5" cy="21.5" r="1.8" />
      </g>
      <g className={styles.right}>
        <rect className={styles.body} x="38" y="30" width="14" height="16" rx="7" />
        <circle className={styles.head} cx="45" cy="24" r="7" />
        <circle className={styles.shine} cx="42.5" cy="21.5" r="1.8" />
      </g>
    </svg>
  );
}
