"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { Story, Topic } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n/context";
import { topicLabel } from "@/lib/topics";
import { StoryCard } from "@/components/stories/StoryCard";
import { Button } from "@/components/ui/Button";
import { TextArea, TextInput } from "@/components/ui/TextArea";
import styles from "./page.module.css";

export function FeedClient() {
  const { locale, t } = useI18n();
  const [items, setItems] = useState<Story[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [filterTopic, setFilterTopic] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [pseudonym, setPseudonym] = useState("");
  const [topic, setTopic] = useState("other");
  const [publishMsg, setPublishMsg] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [composeOpen, setComposeOpen] = useState(false);

  useEffect(() => {
    void api.topics().then(setTopics).catch(() => setTopics([]));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const feed = await api.feed(null, filterTopic || null);
      setItems(feed.items);
      setNextCursor(feed.next_cursor);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : t.feed.offline;
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [filterTopic, t.feed.offline]);

  useEffect(() => {
    void load();
  }, [load]);

  async function loadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    setError(null);
    try {
      const feed = await api.feed(nextCursor, filterTopic || null);
      setItems((prev) => {
        const seen = new Set(prev.map((s) => s.id));
        return [...prev, ...feed.items.filter((s) => !seen.has(s.id))];
      });
      setNextCursor(feed.next_cursor);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.feed.offline);
    } finally {
      setLoadingMore(false);
    }
  }

  async function onPublish() {
    setPublishing(true);
    setPublishMsg(null);
    try {
      const story = await api.publishStory(body, {
        pseudonym: pseudonym || undefined,
        topic,
      });
      setItems((prev) => [story, ...prev]);
      setBody("");
      setPublishMsg(t.feed.published);
      setComposeOpen(false);
    } catch (err) {
      setPublishMsg(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setPublishing(false);
    }
  }

  function onChip(value: string) {
    setFilterTopic((prev) => (prev === value ? "" : value));
  }

  return (
    <>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>{t.feed.title}</h1>
          <p className={styles.sub}>{t.feed.sub}</p>
        </div>
        {/* Compact composer toggle (Telegram-like) */}
        <Button
          variant={composeOpen ? "secondary" : "primary"}
          onClick={() => setComposeOpen((v) => !v)}
          aria-expanded={composeOpen}
        >
          {composeOpen ? t.feed.composeClose : t.feed.composeOpen}
        </Button>
      </header>

      {composeOpen ? (
        <section className={styles.compose} aria-label={t.feed.composeTitle}>
          <h2 className={styles.composeTitle}>{t.feed.composeTitle}</h2>
          <p className={styles.composeHint}>{t.feed.composeHint}</p>
          <TextInput
            id="pseudonym"
            label={t.feed.pseudonym}
            value={pseudonym}
            onChange={(e) => setPseudonym(e.target.value)}
            placeholder={t.feed.pseudonymPlaceholder}
          />
          <label className={styles.fieldLabel} htmlFor="topic">
            {t.feed.topic}
          </label>
          <select
            id="topic"
            className={styles.select}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          >
            {topics.map((item) => (
              <option key={item.value} value={item.value}>
                {topicLabel(item.value, locale) || item.label}
              </option>
            ))}
          </select>
          <TextArea
            id="story-body"
            label={t.feed.monologue}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={t.feed.monologuePlaceholder}
          />
          <Button onClick={onPublish} disabled={publishing || !body.trim()}>
            {t.feed.publish}
          </Button>
          {publishMsg ? <p className={styles.msg}>{publishMsg}</p> : null}
        </section>
      ) : null}

      {/* Topic chips instead of a select */}
      <div className={styles.chips} role="group" aria-label={t.feed.filterAria}>
        <button
          type="button"
          className={`${styles.chip} ${filterTopic === "" ? styles.chipActive : ""}`}
          onClick={() => onChip("")}
          aria-pressed={filterTopic === ""}
        >
          {t.feed.allTopics}
        </button>
        {topics.map((item) => {
          const active = filterTopic === item.value;
          return (
            <button
              key={item.value}
              type="button"
              className={`${styles.chip} ${active ? styles.chipActive : ""}`}
              onClick={() => onChip(item.value)}
              aria-pressed={active}
            >
              {topicLabel(item.value, locale) || item.label}
            </button>
          );
        })}
      </div>

      {loading ? <p className={styles.empty}>{t.feed.loading}</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}
      {!loading && !error && items.length === 0 ? (
        <p className={styles.empty}>{t.feed.empty}</p>
      ) : null}

      {!loading && items.length > 0 ? (
        <p className={styles.feedLabel}>{t.feed.monologuesLabel}</p>
      ) : null}
      <div className={styles.list}>
        {items.map((story) => (
          <StoryCard key={story.id} story={story} href={`/stories/${story.id}`} />
        ))}
      </div>

      {nextCursor && !loading && !error ? (
        <div className={styles.loadMoreWrap}>
          <Button
            variant="secondary"
            onClick={() => void loadMore()}
            disabled={loadingMore}
          >
            {loadingMore ? t.feed.loadMoreLoading : t.feed.loadMore}
          </Button>
        </div>
      ) : null}
    </>
  );
}