import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";
import styles from "./ListRow.module.css";

export interface ListRowProps {
  to?: string;
  title: string;
  subtitle?: string;
  time?: string;
  avatarText: string;
  active?: boolean;
  muted?: boolean;
  softCount?: number;
  onMouseEnter?: () => void;
  onFocus?: () => void;
  style?: CSSProperties;
  /** Extra block under subtitle (e.g. safety banner) */
  extra?: ReactNode;
  className?: string;
  onClick?: () => void;
  asButton?: boolean;
}

/**
 * Telegram Desktop chat-list row: 72px, avatar 54, title/time, 2-line preview.
 */
export function ListRow({
  to,
  title,
  subtitle,
  time,
  avatarText,
  active,
  muted,
  softCount,
  onMouseEnter,
  onFocus,
  style,
  extra,
  className,
  onClick,
  asButton,
}: ListRowProps) {
  const cls = [
    styles.row,
    active ? styles.rowActive : "",
    muted ? styles.rowMuted : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const body = (
    <>
      <span className={styles.avatar} aria-hidden>
        {avatarText.slice(0, 1).toUpperCase()}
      </span>
      <span className={styles.main}>
        <span className={styles.top}>
          <strong className={styles.title}>{title}</strong>
          {time ? <time className={styles.time}>{time}</time> : null}
        </span>
        {subtitle ? <span className={styles.preview}>{subtitle}</span> : null}
        {extra}
      </span>
      {softCount != null && softCount > 0 ? (
        <span className={styles.badge} aria-hidden>
          {softCount > 9 ? "9+" : softCount}
        </span>
      ) : null}
    </>
  );

  if (asButton || !to) {
    return (
      <button
        type="button"
        className={cls}
        style={style}
        onMouseEnter={onMouseEnter}
        onFocus={onFocus}
        onClick={onClick}
      >
        {body}
      </button>
    );
  }

  return (
    <Link
      to={to}
      className={cls}
      style={style}
      aria-current={active ? "page" : undefined}
      onMouseEnter={onMouseEnter}
      onFocus={onFocus}
    >
      {body}
    </Link>
  );
}
