"use client";

import Link from "next/link";
import type { Story } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n/context";
import { topicLabel } from "@/lib/topics";
import styles from "./StoryCard.module.css";

interface StoryCardProps {
  story: Story;
  href?: string;
  full?: boolean;
}

function formatDate(iso: string | null, locale: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(locale === "en" ? "en-GB" : "ru-RU", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function StoryCard({ story, href, full = false }: StoryCardProps) {
  const { locale, t } = useI18n();
  const label = topicLabel(story.topic, locale);
  const className = full ? `${styles.card} ${styles.cardFull}` : styles.card;

  const content = (
    <>
      <div className={styles.meta}>
        <div className={styles.metaLeft}>
          <span className={styles.pseudonym}>{story.pseudonym}</span>
          {label ? <span className={styles.topic}>{label}</span> : null}
        </div>
        <time className={styles.date} dateTime={story.published_at ?? undefined}>
          {formatDate(story.published_at, locale)}
        </time>
      </div>
      <p className={`${styles.body} ${full ? styles.full : ""}`}>{story.body}</p>
      {!full && href ? (
        <span className={styles.readMore}>{t.story.openMonologue}</span>
      ) : null}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={className}>
        {content}
      </Link>
    );
  }

  return <article className={className}>{content}</article>;
}
