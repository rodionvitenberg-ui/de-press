"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n/context";
import styles from "./Footer.module.css";

export function Footer() {
  const t = useT();
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <p>{t.footer.tagline}</p>
        <div className={styles.links}>
          <Link href="/safety">{t.footer.safety}</Link>
          <Link href="/anti-panic">{t.footer.antiPanic}</Link>
        </div>
      </div>
    </footer>
  );
}
