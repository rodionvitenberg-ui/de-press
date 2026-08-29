import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/core/api/client";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useI18n } from "@/core/i18n/context";
import styles from "./HelpPane.module.css";

const HELP_REQUEST_ID_KEY = "depress_help_request_id";

function goBackOr(
  navigate: ReturnType<typeof useNavigate>,
  fallback: string,
): void {
  if (window.history.state?.idx > 0) navigate(-1);
  else navigate(fallback);
}

/**
 * Help gate: on desktop the whole page splits into two halves — AI (link to
 * the full-width /help/ai) and human (one click creates a HelpRequest and
 * leads to /help/wait, where an on-duty Helper can pick it up). Crisis
 * orienters, resources and guides stay below the fold. On phone/tablet the
 * halves stack (≈ the previous card layout) and the optional note stays.
 */
export function HelpPane() {
  const { t } = useI18n();
  const { enter } = useAntiPanic();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");

  const createRequest = useMutation({
    mutationFn: (text: string) => api.createHelpRequest(text),
    onSuccess: (req) => {
      sessionStorage.setItem(HELP_REQUEST_ID_KEY, req.id);
      queryClient.setQueryData(["help-mine"], req);
      navigate("/help/wait");
    },
    onError: () => {
      // Backend is idempotent for pending; still leave the wait surface.
      navigate("/help/wait");
    },
  });

  return (
    <div className={styles.page}>
      <header className={styles.top}>
        <button
          type="button"
          className={styles.back}
          onClick={() => goBackOr(navigate, "/feed")}
        >
          ← {t.common.back}
        </button>
        <h1 className={styles.title}>{t.help.title}</h1>
        <p className={styles.intro}>{t.help.intro}</p>
      </header>

      <section className={styles.gate} aria-label={t.help.title}>
        <Link to="/help/ai" className={`${styles.half} ${styles.halfAi}`}>
          <span className={styles.tag}>{t.help.aiTag}</span>
          <h2 className={styles.halfTitle}>{t.help.aiTitle}</h2>
          <p className={styles.halfLead}>{t.help.aiLead}</p>
          <span className={styles.halfCta}>{t.help.aiCta}</span>
        </Link>

        <article className={`${styles.half} ${styles.halfHuman}`}>
          <span className={styles.tag}>{t.help.humanTag}</span>
          <h2 className={styles.halfTitle}>{t.help.humanTitle}</h2>
          <p className={styles.halfLead}>{t.help.humanLead}</p>
          <button
            type="button"
            className={styles.halfCta}
            disabled={createRequest.isPending}
            onClick={() => createRequest.mutate(note.trim())}
          >
            {t.help.humanCta}
          </button>
          <label className={styles.noteLabel} htmlFor="help-human-note">
            {t.help.humanNoteLabel}
          </label>
          <textarea
            id="help-human-note"
            className={styles.note}
            rows={3}
            value={note}
            placeholder={t.help.humanNotePlaceholder}
            disabled={createRequest.isPending}
            onChange={(e) => setNote(e.target.value)}
          />
        </article>
      </section>

      <div className={styles.rest}>
        <section className={styles.card} aria-labelledby="help-crisis">
          <h2 id="help-crisis" className={styles.sectionTitle}>
            {t.nav.panic}
          </h2>
          <p className={styles.body}>{t.antiPanic.menuHint}</p>
          <button type="button" className={styles.panicBtn} onClick={enter}>
            {t.nav.panic}
          </button>
        </section>

        {t.help.resources.map((block) => (
          <section key={block.region} className={styles.card}>
            <h2 className={styles.sectionTitle}>{block.region}</h2>
            <ul className={styles.list}>
              {block.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ))}

        <section className={styles.card} aria-labelledby="help-safety">
          <h2 id="help-safety" className={styles.sectionTitle}>
            {t.safety.title}
          </h2>
          <p className={styles.body}>{t.safety.body1}</p>
          <p className={styles.body}>{t.safety.body2}</p>
          <p className={styles.body}>{t.safety.body3}</p>
          <p className={styles.body}>{t.safety.body4}</p>
          <p className={styles.body}>{t.safety.body5}</p>
        </section>

        <section className={styles.card} aria-labelledby="help-guides">
          <h2 id="help-guides" className={styles.sectionTitle}>
            {t.guides.title}
          </h2>
          <p className={styles.body}>{t.guides.intro}</p>

          <h3 className={styles.subTitle}>{t.guides.whatYouCanTitle}</h3>
          <ul className={styles.list}>
            {t.guides.whatYouCan.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3 className={styles.subTitle}>{t.guides.whatNotTitle}</h3>
          <ul className={styles.list}>
            {t.guides.whatNot.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3 className={styles.subTitle}>{t.guides.professionalHelpTitle}</h3>
          <p className={styles.body}>{t.guides.professionalHelpBody}</p>
        </section>

        <p className={styles.footerLinks}>
          <Link to="/feed">{t.nav.feed}</Link>
          <span aria-hidden> · </span>
          <Link to="/patterns">{t.nav.patterns}</Link>
        </p>
      </div>
    </div>
  );
}
