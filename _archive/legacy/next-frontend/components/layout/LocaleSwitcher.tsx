"use client";

import { useI18n } from "@/lib/i18n/context";
import type { Locale } from "@/lib/i18n/types";
import styles from "./LocaleSwitcher.module.css";

export function LocaleSwitcher() {
  const { locale, setLocale, t } = useI18n();

  function onChange(next: Locale) {
    if (next !== locale) setLocale(next);
  }

  return (
    <div className={styles.wrap} role="group" aria-label={t.locale.label}>
      <button
        type="button"
        className={locale === "ru" ? styles.active : styles.btn}
        onClick={() => onChange("ru")}
        aria-pressed={locale === "ru"}
      >
        {t.locale.ru}
      </button>
      <span className={styles.sep} aria-hidden>
        /
      </span>
      <button
        type="button"
        className={locale === "en" ? styles.active : styles.btn}
        onClick={() => onChange("en")}
        aria-pressed={locale === "en"}
      >
        {t.locale.en}
      </button>
    </div>
  );
}
