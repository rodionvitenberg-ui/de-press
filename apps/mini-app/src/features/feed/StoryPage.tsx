import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api, ApiError } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import { QuietPhrases } from "./QuietPhrases";
import styles from "./StoryPage.module.css";

export function StoryPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [showRequest, setShowRequest] = useState(false);
  const [intent, setIntent] = useState("listen");
  const [note, setNote] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const query = useQuery({
    queryKey: ["story", id],
    queryFn: () => api.getStory(id ?? ""),
    enabled: Boolean(id),
  });

  const intentsQuery = useQuery({
    queryKey: ["dialogue-intents"],
    queryFn: () => api.dialogueIntents(),
    enabled: showRequest,
  });

  const empathy = useMutation({
    mutationFn: () => api.offerEmpathy(id ?? ""),
    onSuccess: (res) => {
      setStatusMsg(res.message || t.empathy.hearYou);
    },
    onError: (err) => {
      setStatusMsg(err instanceof ApiError ? err.message : t.common.error);
    },
  });

  const requestDialogue = useMutation({
    mutationFn: () => api.requestDialogue(id ?? "", intent, note.trim()),
    onSuccess: () => {
      setStatusMsg(t.dialogue.requestSent);
      setShowRequest(false);
      setNote("");
    },
    onError: (err) => {
      setStatusMsg(err instanceof ApiError ? err.message : t.common.error);
    },
  });

  const report = useMutation({
    mutationFn: () => api.reportStory(id ?? "", "other"),
    onSuccess: (res) => {
      setStatusMsg(res.message);
      setMenuOpen(false);
    },
    onError: (err) => {
      setStatusMsg(err instanceof ApiError ? err.message : t.common.error);
    },
  });

  const story = query.data;
  const raysSent = empathy.isSuccess;
  const raysBusy = empathy.isPending;

  return (
    <div className={styles.page}>
      {query.isLoading ? (
        <p className={styles.empty}>{t.story.loading}</p>
      ) : query.isError || !story ? (
        <p className={styles.empty}>{t.story.notFound}</p>
      ) : (
        <>
          <article className={styles.card}>
            <header className={styles.head}>
              <span className={styles.avatar} aria-hidden>
                {story.pseudonym.slice(0, 1).toUpperCase()}
              </span>
              <div>
                <strong>{story.pseudonym}</strong>
                <small>{story.topic}</small>
              </div>
            </header>
            <div className={styles.text}>{story.body}</div>
          </article>

          <QuietPhrases storyId={story.id} />

          {showRequest ? (
            <div className={styles.requestBox}>
              <p className={styles.requestLead}>{t.dialogue.similarHint}</p>
              <label className={styles.field}>
                <span className={styles.label}>{t.dialogue.similar}</span>
                <select
                  className={styles.select}
                  value={intent}
                  onChange={(e) => setIntent(e.target.value)}
                >
                  {(intentsQuery.data ?? [{ value: "listen", label: "listen" }]).map(
                    (opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ),
                  )}
                </select>
              </label>
              <label className={styles.field}>
                <span className={styles.label}>{t.dialogue.noteLabel}</span>
                <textarea
                  className={styles.note}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder={t.dialogue.notePlaceholder}
                  rows={2}
                />
              </label>
              <div className={styles.requestActions}>
                <button
                  type="button"
                  className={`${styles.action} ${styles.actionPrimary}`}
                  disabled={requestDialogue.isPending}
                  onClick={() => requestDialogue.mutate()}
                >
                  {t.dialogue.sendRequest}
                </button>
                <button
                  type="button"
                  className={styles.action}
                  onClick={() => setShowRequest(false)}
                >
                  {t.dialogue.cancel}
                </button>
              </div>
            </div>
          ) : null}

          <footer className={styles.actions}>
            <button
              type="button"
              className={styles.action}
              onClick={() => {
                setShowRequest((v) => !v);
                setStatusMsg(null);
              }}
            >
              {t.nav.me}
            </button>
            <button
              type="button"
              className={`${styles.action} ${styles.actionPrimary}`}
              disabled={raysBusy || raysSent}
              onClick={() => {
                setStatusMsg(null);
                empathy.mutate();
              }}
            >
              {raysBusy
                ? "…"
                : raysSent
                  ? t.empathy.hearYou
                  : t.shell.sendRays}
            </button>
            <div className={styles.menuWrap}>
              <button
                type="button"
                className={styles.action}
                aria-label="Меню"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((v) => !v)}
              >
                ⋯
              </button>
              {menuOpen ? (
                <div className={styles.menu} role="menu">
                  <button
                    type="button"
                    role="menuitem"
                    className={styles.menuItem}
                    onClick={() => report.mutate()}
                  >
                    {t.report.report}
                  </button>
                </div>
              ) : null}
            </div>
          </footer>

          {statusMsg ? (
            <p className={styles.status} role="status" aria-live="polite">
              {statusMsg}
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}
