import Link from "next/link";
import { getMessages } from "@/lib/i18n";
import { getServerLocale } from "@/lib/i18n/server";
import styles from "./page.module.css";

export default async function SafetyPage() {
  const locale = await getServerLocale();
  const t = getMessages(locale);
  return (
    <article className={styles.page}>
      <h1 className={styles.title}>{t.safety.title}</h1>
      <p>{t.safety.body1}</p>
      <div className={styles.box}>
        <p>{t.safety.body2}</p>
      </div>
      <p>{t.safety.body3}</p>
      <p>{t.safety.body4}</p>
      <p>{t.safety.body5}</p>
      <p>
        {t.safety.see}
        <Link href="/guides">{t.safety.guidesLink}</Link>. {t.safety.crisisIn}
        <Link href="/anti-panic">{t.safety.antiPanicLink}</Link>.
      </p>
    </article>
  );
}