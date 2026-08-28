"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useT } from "@/lib/i18n/context";
import styles from "./BottomNav.module.css";

export function BottomNav() {
  const t = useT();
  const pathname = usePathname();

  const items: { href: string; label: string; icon: string }[] = [
    { href: "/feed", label: t.nav.feed, icon: "M4 5h16M4 12h16M4 19h10" },
    { href: "/me", label: t.nav.me, icon: "M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8 8 8 0 0 1 8 8Z" },
    { href: "/patterns", label: t.nav.patterns, icon: "M4 19V9M10 19V5M16 19v-7M22 19H2" },
    { href: "/help", label: t.nav.help, icon: "M9.5 9.5a2.5 2.5 0 1 1 3.2 2.4c-.7.3-1.2 1-1.2 1.8v.3" },
  ];

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));

  return (
    <nav className={styles.nav} aria-label={t.nav.ariaMain}>
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`${styles.item} ${isActive(item.href) ? styles.active : ""}`}
          aria-current={isActive(item.href) ? "page" : undefined}
        >
          <svg
            className={styles.icon}
            width={22}
            height={22}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d={item.icon} />
          </svg>
          <span className={styles.label}>{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}