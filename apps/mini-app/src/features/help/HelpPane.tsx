import { Link } from "react-router-dom";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useI18n } from "@/core/i18n/context";
import styles from "./HelpPane.module.css";

/**
 * Help surface: crisis orienters + safety notes + short support guides.
 * Content from i18n; not medical advice.
 */
export function HelpPane() {
  const { t } = useI18n();
  const { enter } = useAntiPanic();

  return (
    <div className={styles.pane}>
      <header className={styles.head}>
        <h1 className={styles.title}>{t.help.title}</h1>
        <p className={styles.intro}>{t.help.intro}</p>
      </header>

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
  );
}
