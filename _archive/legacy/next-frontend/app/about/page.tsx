import { getMessages } from "@/lib/i18n";
import { getServerLocale } from "@/lib/i18n/server";
import styles from "./page.module.css";

export default async function AboutPage() {
  const locale = await getServerLocale();
  const t = getMessages(locale);
  return (
    <article className={styles.page}>
      <h1 className={styles.title}>{t.about.title}</h1>
      <p>{t.about.intro}</p>
      <ul>
        {t.about.points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
      <p>{t.about.footer}</p>
    </article>
  );
}