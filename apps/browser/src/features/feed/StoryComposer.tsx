import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "@/core/api/client";
import { useVoiceRecorder } from "@/core/hooks/useVoiceRecorder";
import { useI18n } from "@/core/i18n/context";
import { applyFeedEvent, type FeedInfinite } from "./applyFeedEvent";
import styles from "./StoryComposer.module.css";

export function StoryComposer() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const [pseudonym, setPseudonym] = useState("");
  const [topic, setTopic] = useState("");
  const [error, setError] = useState<string | null>(null);

  const topicsQuery = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.topics(),
  });

  const publish = useMutation({
    mutationFn: () =>
      api.publishStory(body.trim(), {
        pseudonym: pseudonym.trim() || undefined,
        topic: topic || undefined,
      }),
    onSuccess: async (story) => {
      queryClient.setQueryData<FeedInfinite>(["feed"], (prev) =>
        applyFeedEvent(prev, { type: "story.published", story }, null) ?? prev,
      );
      await queryClient.invalidateQueries({ queryKey: ["feed"] });
      navigate(`/feed/${story.id}`, { replace: true });
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError
          ? err.message
          : "Не удалось опубликовать мысль.";
      setError(msg);
    },
  });

  const publishVoice = useMutation({
    mutationFn: ({ blob, durationMs }: { blob: Blob; durationMs: number }) =>
      api.publishStoryVoice(blob, {
        body: body.trim() || undefined,
        pseudonym: pseudonym.trim() || undefined,
        topic: topic || undefined,
        durationMs,
        filename: "note.webm",
      }),
    onSuccess: async (story) => {
      queryClient.setQueryData<FeedInfinite>(["feed"], (prev) =>
        applyFeedEvent(prev, { type: "story.published", story }, null) ?? prev,
      );
      await queryClient.invalidateQueries({ queryKey: ["feed"] });
      navigate(`/feed/${story.id}`, { replace: true });
    },
    onError: (err) => {
      setError(
        err instanceof ApiError ? err.message : t.common.error,
      );
    },
  });

  const rec = useVoiceRecorder((blob, durationMs) => {
    publishVoice.mutate({ blob, durationMs });
  }, t.chat.unsupported);

  const busy = publish.isPending || publishVoice.isPending || rec.recording;
  const canSubmit = body.trim().length > 0 && !busy;

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <Link to="/feed" className={styles.backLink} aria-label={t.nav.feed}>
          ←
        </Link>
        <h1 className={styles.title}>Добавить запись</h1>
      </header>
      <p className={styles.hint}>
        Тихий монолог без комментариев. Диалог — только если вы сами откроете.
      </p>

      <label className={styles.field}>
        <span className={styles.label}>Мысль</span>
        <textarea
          className={styles.textarea}
          placeholder="Ваша мысль…"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={6}
          maxLength={8000}
          disabled={publish.isPending}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.label}>Псевдоним (необязательно)</span>
        <input
          type="text"
          className={styles.input}
          placeholder="Как вас назвать"
          value={pseudonym}
          onChange={(e) => setPseudonym(e.target.value)}
          maxLength={64}
          disabled={publish.isPending}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.label}>Тема</span>
        <select
          className={styles.select}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={publish.isPending || topicsQuery.isLoading}
        >
          <option value="">Без темы</option>
          {(topicsQuery.data ?? []).map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </label>

      {error || rec.error ? (
        <p className={styles.error} role="alert">
          {error || rec.error}
        </p>
      ) : null}

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.mic}
          disabled={publish.isPending || publishVoice.isPending}
          onClick={() => void rec.toggle()}
          aria-label={rec.recording ? t.chat.stop : t.chat.micAria}
        >
          {rec.recording ? t.chat.stop : t.chat.micAria}
        </button>
        <button
          type="button"
          className={styles.submit}
          disabled={!canSubmit}
          onClick={() => {
            setError(null);
            publish.mutate();
          }}
        >
          {publish.isPending || publishVoice.isPending
            ? "Публикуем…"
            : "Опубликовать"}
        </button>
      </div>
    </div>
  );
}
