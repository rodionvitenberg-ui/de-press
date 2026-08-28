import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api, ApiError } from "@/core/api/client";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useI18n } from "@/core/i18n/context";
import { EmotionSticker, isGestureKey } from "./EmotionSticker";
import styles from "./AuthorClouds.module.css";

interface AuthorCloudsProps {
  storyId: string;
  highlightId?: string | null;
}

export function AuthorClouds({ storyId, highlightId }: AuthorCloudsProps) {
  const { locale, t } = useI18n();
  const { active: panic } = useAntiPanic();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["story-clouds", storyId],
    queryFn: () => api.storyClouds(storyId),
    retry: false,
    placeholderData: keepPreviousData,
    refetchInterval: panic ? false : 20_000,
  });

  const dismiss = useMutation({
    mutationFn: (cloudId: string) => api.dismissCloud(storyId, cloudId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["story-clouds", storyId] });
    },
  });

  if (query.isError) {
    if (query.error instanceof ApiError && query.error.status === 403) {
      return null;
    }
    return (
      <p className={styles.meta}>
        {query.error instanceof ApiError ? query.error.message : t.common.error}
      </p>
    );
  }

  if (query.isLoading) {
    return <p className={styles.meta}>{t.clouds.loading}</p>;
  }

  const clouds = query.data ?? [];

  return (
    <section className={styles.wrap} aria-label={t.clouds.show}>
      <h2 className={styles.title}>{t.clouds.show}</h2>
      {clouds.length === 0 ? (
        <p className={styles.meta}>{t.clouds.empty}</p>
      ) : (
        <ul className={styles.list}>
          {clouds.map((c) => (
            <li
              key={c.id}
              id={`cloud-${c.id}`}
              className={
                c.id === highlightId
                  ? `${styles.cloud} ${styles.cloudHi}`
                  : c.is_priority
                    ? `${styles.cloud} ${styles.cloudPriority}`
                    : styles.cloud
              }
            >
              {c.helper_badge ? (
                <p className={styles.badge}>{c.helper_badge}</p>
              ) : null}
              <div className={styles.row}>
                {c.phrase_key && isGestureKey(c.phrase_key) ? (
                  <EmotionSticker
                    gesture={c.phrase_key}
                    label={c.body}
                    compact
                  />
                ) : c.image_url ? (
                  <img src={c.image_url} alt="" className={styles.img} />
                ) : null}
                <div className={styles.main}>
                  <p className={styles.body}>{c.body}</p>
                  <button
                    type="button"
                    className={styles.dismiss}
                    onClick={() => dismiss.mutate(c.id)}
                    disabled={dismiss.isPending}
                  >
                    {t.clouds.dismiss}
                  </button>
                  <p className={styles.meta}>
                    {c.pseudonym}
                    {c.kind === "free_text" ? ` · ${t.clouds.freeText}` : ""}
                    {c.created_at
                      ? ` · ${new Date(c.created_at).toLocaleString(
                          locale === "en" ? "en-GB" : "ru-RU",
                          {
                            day: "numeric",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          },
                        )}`
                      : null}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
