import { getMessages } from "@/lib/i18n";
import { getServerLocale } from "@/lib/i18n/server";
import styles from "./page.module.css";

export default async function GuidesPage() {
  const locale = await getServerLocale();
  const t = getMessages(locale);
  return (
    <article className={styles.page}>
      <h1 className={styles.title}>{t.guides.title}</h1>
      <p>{t.guides.intro}</p>

      <section>
        <h2>{t.guides.whatYouCanTitle}</h2>
        <ul>
          {t.guides.whatYouCan.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>{t.guides.whatNotTitle}</h2>
        <ul>
          {t.guides.whatNot.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>{t.guides.professionalHelpTitle}</h2>
        <p>{t.guides.professionalHelpBody}</p>
      </section>
    </article>
  );
}