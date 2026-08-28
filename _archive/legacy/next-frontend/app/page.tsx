"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n/context";
import styles from "./page.module.css";

export default function HomePage() {
  const t = useT();
  return (
    <section className={styles.hero}>
      <p className={styles.eyebrow}>{t.home.eyebrow}</p>
      <h1 className={styles.title}>{t.home.title}</h1>
      <p className={styles.lead}>{t.home.lead}</p>
      <div className={styles.cloudsHint}>
        <p>
          <strong>{t.home.publicLabel}</strong> {t.home.publicText}
        </p>
        <p>
          <strong>{t.home.authorLabel}</strong> {t.home.authorText}
        </p>
      </div>
      <div className={styles.actions}>
        <Link href="/feed" className={styles.primaryLink}>
          {t.home.toFeed}
        </Link>
        <Link href="/anti-panic">{t.home.antiPanic}</Link>
        <Link href="/about">{t.home.about}</Link>
      </div>
      <p className={styles.note}>
        {t.home.note} <Link href="/safety">{t.home.safetyLink}</Link>.
      </p>
    </section>
  );
}
