import { useEffect, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import styles from "./InboxPage.module.css";

/**
 * Private inbox entry (`/inbox?token=…`) opened from a soft-notify email.
 * The magic token logs the actor in (account → session, anon → bind cookie)
 * and marks the digest's notifications read — no password involved.
 */
export function InboxPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [params] = useSearchParams();
  const token = params.get("token");
  const fired = useRef(false);

  const open = useMutation({
    mutationFn: () => api.openInbox(token ?? ""),
    onSuccess: () => {
      // Actor identity changed server-side — refresh who-am-i and badges.
      void queryClient.invalidateQueries({ queryKey: ["me"] });
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
      void queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });

  useEffect(() => {
    // Magic tokens are single-use: fire exactly once, even under StrictMode.
    if (!token || fired.current) return;
    fired.current = true;
    open.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per token
  }, [token]);

  let body;
  if (!token || open.isError) {
    body = <p className={styles.note}>{t.inbox.invalid}</p>;
  } else if (open.isSuccess) {
    body = (
      <>
        <p className={styles.note}>{t.inbox.welcome}</p>
        <button
          type="button"
          className={styles.action}
          onClick={() => navigate("/feed")}
        >
          {t.inbox.goFeed}
        </button>
      </>
    );
  } else {
    body = <p className={styles.note}>{t.inbox.opening}</p>;
  }

  return (
    <div className={styles.pane}>
      <h1 className={styles.title}>{t.inbox.title}</h1>
      {body}
    </div>
  );
}
