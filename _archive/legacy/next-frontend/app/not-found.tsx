import Link from "next/link";
import { getMessages } from "@/lib/i18n";
import { getServerLocale } from "@/lib/i18n/server";
import styles from "./not-found.module.css";

export default async function NotFound() {
  const locale = await getServerLocale();
  const t = getMessages(locale);
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>404</h1>
      <p className={styles.lead}>
        {locale === "ru"
          ? "Здесь тихо. Такой страницы нет."
          : "It’s quiet here. This page doesn’t exist."}
      </p>
      <Link href="/feed" className={styles.link}>
        {t.nav.feed}
      </Link>
    </div>
  );
}