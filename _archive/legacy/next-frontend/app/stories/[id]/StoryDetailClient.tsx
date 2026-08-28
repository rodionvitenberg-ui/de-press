"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { Story } from "@/lib/types/api";
import { useT } from "@/lib/i18n/context";
import { StoryCard } from "@/components/stories/StoryCard";
import { HearYouButton } from "@/components/empathy/HearYouButton";
import { ReportButton } from "@/components/moderation/ReportButton";
import { SimilarStoryButton } from "@/components/dialogue/SimilarStoryButton";
import { QuietPhrases } from "@/components/support/QuietPhrases";
import styles from "./page.module.css";

interface Props {
  storyId: string;
}

export function StoryDetailClient({ storyId }: Props) {
  const t = useT();
  const [story, setStory] = useState<Story | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await api.getStory(storyId);
        if (!cancelled) setStory(s);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : t.story.notFound);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [storyId, t.story.notFound]);

  if (error) {
    return (
      <div className={styles.page}>
        <Link href="/feed" className={styles.back}>
          {t.story.back}
        </Link>
        <p className={styles.error}>{error}</p>
      </div>
    );
  }

  if (!story) {
    return (
      <div className={styles.page}>
        <p className={styles.loading}>{t.story.loading}</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link href="/feed" className={styles.back}>
        {t.story.back}
      </Link>

      <section className={styles.monologue} aria-label={t.feed.monologue}>
        <p className={styles.eyebrow}>{t.story.eyebrow}</p>
        <StoryCard story={story} full />
      </section>

      <section className={styles.support} aria-label={t.support.title}>
        <header className={styles.sectionHead}>
          <h2 className={styles.sectionTitle}>{t.story.supportTitle}</h2>
          <p className={styles.sectionLead}>{t.story.supportLead}</p>
        </header>
        <div className={styles.primaryActions}>
          <HearYouButton storyId={story.id} />
          <QuietPhrases storyId={story.id} />
        </div>
      </section>

      <section className={styles.secondary} aria-label={t.nav.safety}>
        <SimilarStoryButton storyId={story.id} />
        <ReportButton storyId={story.id} />
      </section>
    </div>
  );
}
