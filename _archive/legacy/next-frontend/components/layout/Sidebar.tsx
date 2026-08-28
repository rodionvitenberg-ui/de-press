"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAntiPanic } from "@/hooks/useAntiPanic";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { LocaleSwitcher } from "./LocaleSwitcher";
import styles from "./Sidebar.module.css";

type IconName =
  | "feed"
  | "chats"
  | "helper"
  | "ai"
  | "patterns"
  | "help"
  | "guides"
  | "safety"
  | "about";

function SidebarIcon({ name }: { name: IconName }) {
  const common = {
    width: 20,
    height: 20,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  switch (name) {
    case "feed":
      return (
        <svg {...common}>
          <path d="M4 5h16M4 12h16M4 19h10" />
        </svg>
      );
    case "chats":
      return (
        <svg {...common}>
          <path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8 8 8 0 0 1 8 8Z" />
        </svg>
      );
    case "helper":
      return (
        <svg {...common}>
          <path d="M12 3 4 7v6c0 4 3.5 6.5 8 8 4.5-1.5 8-4 8-8V7l-8-4Z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );
    case "ai":
      return (
        <svg {...common}>
          <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
          <circle cx="12" cy="12" r="3.5" />
        </svg>
      );
    case "patterns":
      return (
        <svg {...common}>
          <path d="M4 19V9M10 19V5M16 19v-7M22 19H2" />
        </svg>
      );
    case "help":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M9.5 9.5a2.5 2.5 0 1 1 3.2 2.4c-.7.3-1.2 1-1.2 1.8v.3" />
          <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
        </svg>
      );
    case "guides":
      return (
        <svg {...common}>
          <path d="M5 4h11a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2V4Z" />
          <path d="M5 4a2 2 0 0 1 2-2h11v16" />
        </svg>
      );
    case "safety":
      return (
        <svg {...common}>
          <path d="M12 3 4 7v6c0 5 3.5 8 8 8s8-3 8-8V7l-8-4Z" />
        </svg>
      );
    case "about":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5M12 8v.5" />
        </svg>
      );
  }
}

export function Sidebar() {
  const t = useT();
  const { enter } = useAntiPanic();
  const pathname = usePathname();

  const items: { href: string; label: string; icon: IconName }[] = [
    { href: "/feed", label: t.nav.feed, icon: "feed" },
    { href: "/me", label: t.nav.me, icon: "chats" },
    { href: "/helper", label: t.nav.helper, icon: "helper" },
    { href: "/companion", label: t.nav.companion, icon: "ai" },
    { href: "/patterns", label: t.nav.patterns, icon: "patterns" },
  ];

  const bottomItems: { href: string; label: string; icon: IconName }[] = [
    { href: "/help", label: t.nav.help, icon: "help" },
    { href: "/guides", label: t.nav.guides, icon: "guides" },
    { href: "/safety", label: t.nav.safety, icon: "safety" },
    { href: "/about", label: t.nav.about, icon: "about" },
  ];

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));

  return (
    <aside className={styles.sidebar}>
      <Link href="/" className={styles.brand}>
        de-press
      </Link>

      <nav className={styles.nav} aria-label={t.nav.ariaMain}>
        <p className={styles.label}>{t.nav.account}</p>
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`${styles.item} ${
              isActive(item.href) ? styles.itemActive : ""
            }`}
            aria-current={isActive(item.href) ? "page" : undefined}
          >
            <span className={styles.icon}>
              <SidebarIcon name={item.icon} />
            </span>
            <span>{item.label}</span>
          </Link>
        ))}

        <p className={styles.label}>{t.nav.more}</p>
        {bottomItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`${styles.item} ${
              isActive(item.href) ? styles.itemActive : ""
            }`}
            aria-current={isActive(item.href) ? "page" : undefined}
          >
            <span className={styles.icon}>
              <SidebarIcon name={item.icon} />
            </span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className={styles.bottom}>
        <div className={styles.item}>
          <NotificationBell />
          <LocaleSwitcher />
        </div>
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
    </aside>
  );
}