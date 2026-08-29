import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "@/core/api/client";
import type { HelpRequest } from "@/core/api/types";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useI18n } from "@/core/i18n/context";
import styles from "./HelpWaitPane.module.css";

async function fetchMine(): Promise<HelpRequest | null> {
  try {
    return await api.myHelpRequest();
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

/**
 * Waiting surface after creating a HelpRequest: poll until accepted or cancel.
 */
export function HelpWaitPane() {
  const { t } = useI18n();
  const { active: panic } = useAntiPanic();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mineQuery = useQuery({
    queryKey: ["help-mine"],
    queryFn: fetchMine,
    retry: false,
    refetchInterval: panic ? false : 4000,
  });

  const presenceQuery = useQuery({
    queryKey: ["help-presence"],
    queryFn: () => api.helpPresence(),
    refetchInterval: panic ? false : 4000,
  });

  const cancel = useMutation({
    mutationFn: (id: string) => api.cancelHelpRequest(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["help-mine"] });
      navigate("/help");
    },
  });

  const req = mineQuery.data;
  const loading = mineQuery.isPending && req === undefined;
  const matched = req?.status === "accepted" && Boolean(req.dialogue_id);
  const presence = presenceQuery.data;
  const presenceLine = matched || !presence
    ? null
    : presence.someone_online
      ? t.help.waitPresenceOnline
      : presence.someone_on_duty
        ? t.help.waitPresenceDuty
        : t.help.waitPresenceEmpty;

  return (
    <div className={styles.pane}>
      <header className={styles.head}>
        <h1 className={styles.title}>
          {matched ? t.help.waitMatchedTitle : t.help.waitTitle}
        </h1>
        <p className={styles.intro}>{t.help.waitBody}</p>
        {presenceLine ? <p className={styles.intro}>{presenceLine}</p> : null}
      </header>

      <section className={styles.card}>
        {loading ? (
          <p className={styles.body}>{t.common.loading}</p>
        ) : mineQuery.isError ? (
          <p className={styles.body} role="alert">
            {mineQuery.error instanceof ApiError
              ? mineQuery.error.message
              : t.common.error}
          </p>
        ) : !req || req.status === "cancelled" ? (
          <>
            <p className={styles.body}>{t.help.waitBody}</p>
            <Link to="/help" className={styles.secondaryCta}>
              {t.nav.help}
            </Link>
          </>
        ) : req.status === "accepted" && req.dialogue_id ? (
          <Link
            to={`/chat/${req.dialogue_id}`}
            className={styles.primaryCta}
          >
            {t.help.waitOpenChat}
          </Link>
        ) : (
          <>
            <button
              type="button"
              className={styles.cancelBtn}
              disabled={cancel.isPending}
              onClick={() => cancel.mutate(req.id)}
            >
              {t.help.waitCancel}
            </button>
            <Link to="/help/ai" className={styles.secondaryCta}>
              {t.help.waitToAi}
            </Link>
            {cancel.isError ? (
              <p className={styles.error} role="alert">
                {cancel.error instanceof ApiError
                  ? cancel.error.message
                  : t.common.error}
              </p>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
