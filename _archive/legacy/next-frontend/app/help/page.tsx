import Link from "next/link";
import { getMessages } from "@/lib/i18n";
import { getServerLocale } from "@/lib/i18n/server";
import styles from "./page.module.css";

export default async function HelpPage() {
  const locale = await getServerLocale();
  const t = getMessages(locale);
  return (
    <article className={styles.page}>
      <h1 className={styles.title}>{t.help.title}</h1>
      <p>{t.help.intro}</p>
      {t.help.resources.map((block) => (
        <div key={block.region} className={styles.box}>
          <p>
            <strong>{block.region}</strong>
          </p>
          <ul>
            {block.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
      <p>
        <Link href="/anti-panic">{t.nav.panic}</Link> ·{" "}
        <Link href="/safety">{t.nav.safety}</Link> ·{" "}
        <Link href="/guides">{t.nav.guides}</Link>
      </p>
    </article>
  );
}