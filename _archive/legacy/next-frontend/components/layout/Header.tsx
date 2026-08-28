"use client";

import Link from "next/link";
import { useAntiPanic } from "@/hooks/useAntiPanic";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { LocaleSwitcher } from "./LocaleSwitcher";
import styles from "./Header.module.css";

export function Header() {
  const { active, enter, exit } = useAntiPanic();
  const t = useT();

  if (active) {
    return (
      <header className={styles.header}>
        <div className={styles.inner}>
          <span className={styles.brand}>{t.nav.quiet}</span>
          <Button variant="ghost" onClick={exit}>
            {t.nav.exitPanic}
          </Button>
        </div>
      </header>
    );
  }

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand}>
          de-press
        </Link>
        <div className={styles.tools}>
          <NotificationBell />
          <LocaleSwitcher />
          <Button
            variant="danger"
            className={styles.panic}
            onClick={() => {
              enter();
              window.location.href = "/anti-panic";
            }}
          >
            {t.nav.panic}
          </Button>
        </div>
      </div>
    </header>
  );
}