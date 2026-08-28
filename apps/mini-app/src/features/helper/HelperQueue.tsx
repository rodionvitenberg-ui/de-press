import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import styles from "./HelperQueue.module.css";

export function HelperQueue() {
  const { t } = useI18n();
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: () => api.me(),
  });

  const queueQuery = useQuery({
    queryKey: ["moderation-queue"],
    queryFn: () => api.moderationQueue(),
    enabled: Boolean(meQuery.data?.is_helper),
  });

  const approve = useMutation({
    mutationFn: (id: string) => api.approveCloud(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["moderation-queue"] });
    },
  });

  const reject = useMutation({
    mutationFn: (id: string) => api.rejectCloud(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["moderation-queue"] });
    },
  });

  if (meQuery.isLoading) {
    return <p className={styles.empty}>{t.helper.loading}</p>;
  }

  if (!meQuery.data?.is_helper) {
    return (
      <div className={styles.pane}>
        <h1 className={styles.title}>{t.helper.title}</h1>
        <p className={styles.empty}>{t.helper.needRole}</p>
      </div>
    );
  }

  const items = queueQuery.data ?? [];

  return (
    <div className={styles.pane}>
      <header className={styles.head}>
        <h1 className={styles.title}>{t.helper.title}</h1>
        <p className={styles.lead}>{t.helper.lead}</p>
      </header>

      {queueQuery.isLoading ? (
        <p className={styles.empty}>{t.helper.loading}</p>
      ) : queueQuery.isError ? (
        <p className={styles.empty}>
          {queueQuery.error instanceof ApiError
            ? queueQuery.error.message
            : t.common.error}
        </p>
      ) : items.length === 0 ? (
        <p className={styles.empty}>{t.helper.empty}</p>
      ) : (
        <ul className={styles.list}>
          {items.map((cloud) => (
            <li key={cloud.id} className={styles.card}>
              <p className={styles.meta}>
                {t.helper.from} {cloud.pseudonym}
                {cloud.helper_badge ? ` · ${cloud.helper_badge}` : ""}
              </p>
              <p className={styles.preview}>{cloud.story_preview}</p>
              <p className={styles.body}>{cloud.body}</p>
              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.approve}
                  disabled={approve.isPending || reject.isPending}
                  onClick={() => approve.mutate(cloud.id)}
                >
                  {t.helper.approve}
                </button>
                <button
                  type="button"
                  className={styles.reject}
                  disabled={approve.isPending || reject.isPending}
                  onClick={() => reject.mutate(cloud.id)}
                >
                  {t.helper.reject}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
