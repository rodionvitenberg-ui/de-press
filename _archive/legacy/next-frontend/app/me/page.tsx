"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { useNotifications } from "@/hooks/useNotifications";
import type { AuthorStory, Dialogue, DialogueRequest } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n/context";
import { topicLabel } from "@/lib/topics";
import { Button } from "@/components/ui/Button";
import { AuthorClouds } from "@/components/support/AuthorClouds";
import { AuthorHearers } from "@/components/empathy/AuthorHearers";
import { NotifySettings } from "@/components/profile/NotifySettings";
import styles from "./page.module.css";

export default function MePage() {
  const { locale, t } = useI18n();
  const [stories, setStories] = useState<AuthorStory[]>([]);
  const [inbox, setInbox] = useState<DialogueRequest[]>([]);
  const [dialogues, setDialogues] = useState<Dialogue[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { unreadCount } = useNotifications();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, i, d] = await Promise.all([
        api.myStories(),
        api.dialogueInbox(),
        api.myDialogues(),
      ]);
      setStories(s);
      setInbox(i);
      setDialogues(d);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  }, [t.common.error]);

  useEffect(() => {
    void load();
  }, [load]);

  // Live refresh: when a new notification arrives (dialogue request / cloud),
  // reload inbox, dialogues and clouds.
  useEffect(() => {
    if (unreadCount > 0) {
      void load();
    }
  }, [unreadCount, load]);

  async function accept(id: string) {
    try {
      const d = await api.acceptDialogueRequest(id);
      setInbox((prev) => prev.filter((r) => r.id !== id));
      setDialogues((prev) => [d, ...prev]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }

  async function decline(id: string) {
    try {
      await api.declineDialogueRequest(id);
      setInbox((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.intro}>
        <h1 className={styles.title}>{t.me.title}</h1>
        <span className={styles.privateBadge}>{t.me.privateBadge}</span>
        <p className={styles.meta}>{t.me.intro}</p>
      </header>

      <section className={styles.section} aria-labelledby="notify-title">
        <NotifySettings />
      </section>

      {loading ? <p className={styles.empty}>{t.me.loading}</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}

      <section className={styles.section} aria-labelledby="inbox-title">
        <h2 id="inbox-title" className={styles.sectionTitle}>
          {t.me.inboxTitle}
        </h2>
        <p className={styles.sectionNote}>{t.me.inboxNote}</p>
        {inbox.length === 0 ? (
          <p className={styles.empty}>{t.me.inboxEmpty}</p>
        ) : (
          <div className={styles.list}>
            {inbox.map((r) => (
              <div key={r.id} className={styles.card}>
                <p className={styles.meta}>
                  {r.intent} ·{" "}
                  <Link href={`/stories/${r.story_id}`}>{t.me.toStory}</Link>
                </p>
                {r.note ? <p>{r.note}</p> : null}
                <div className={styles.actions}>
                  <Button onClick={() => accept(r.id)}>{t.me.openDialogue}</Button>
                  <Button variant="ghost" onClick={() => decline(r.id)}>
                    {t.me.decline}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className={styles.section} aria-labelledby="dialogues-title">
        <h2 id="dialogues-title" className={styles.sectionTitle}>
          {t.me.dialoguesTitle}
        </h2>
        {dialogues.length === 0 ? (
          <p className={styles.empty}>{t.me.dialoguesEmpty}</p>
        ) : (
          <div className={styles.list}>
            {dialogues.map((d) => (
              <Link
                key={d.id}
                href={`/dialogues/${d.id}`}
                className={styles.chatRow}
              >
                <span className={styles.chatAvatar} aria-hidden>
                  {(d.intent || "?").slice(0, 1).toUpperCase()}
                </span>
                <span className={styles.chatRowBody}>
                  <span className={styles.chatRowTitle}>
                    {d.intent}
                    {d.source === "author_outreach" ? " · outreach" : ""}
                  </span>
                  <span className={styles.chatRowSub}>
                    {d.status} · {t.me.openChat}
                  </span>
                </span>
                <span className={styles.chatRowStatus}>
                  {d.status === "open" ? "●" : "◇"}
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className={styles.section} aria-labelledby="stories-title">
        <h2 id="stories-title" className={styles.sectionTitle}>
          {t.me.storiesTitle}
        </h2>
        <p className={styles.sectionNote}>{t.me.storiesNote}</p>
        {stories.length === 0 ? (
          <p className={styles.empty}>
            {t.me.storiesEmpty} <Link href="/feed">{t.me.write}</Link>
          </p>
        ) : (
          <div className={styles.list}>
            {stories.map((s) => (
              <article key={s.id} className={styles.card}>
                <Link href={`/stories/${s.id}`} className={styles.storyLink}>
                  <p className={styles.meta}>
                    {topicLabel(s.topic, locale)} · {s.status}
                  </p>
                  <p>
                    {s.body.length > 160 ? `${s.body.slice(0, 160)}…` : s.body}
                  </p>
                  <p className={styles.pulse}>{s.pulse_message}</p>
                </Link>
                <div className={styles.privatePanel}>
                  <AuthorClouds storyId={s.id} />
                  <AuthorHearers storyId={s.id} />
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
