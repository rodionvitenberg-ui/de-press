"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api/client";
import { useT } from "@/lib/i18n/context";
import styles from "./page.module.css";

type InboxState = "opening" | "ok" | "invalid";

export default function InboxPage() {
  const t = useT();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [state, setState] = useState<InboxState>("opening");

  useEffect(() => {
    if (!token) {
      setState("invalid");
      return;
    }
    let cancelled = false;
    api
      .openInbox(token)
      .then(() => {
        if (!cancelled) setState("ok");
      })
      .catch(() => {
        if (!cancelled) setState("invalid");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>{t.inbox.title}</h1>
      {state === "opening" ? (
        <p className={styles.status}>{t.inbox.opening}</p>
      ) : null}
      {state === "ok" ? (
        <>
          <p className={styles.welcome}>{t.inbox.welcome}</p>
          <div className={styles.links}>
            <Link href="/me">{t.inbox.goMe}</Link>
            <Link href="/feed">{t.inbox.goFeed}</Link>
          </div>
        </>
      ) : null}
      {state === "invalid" ? (
        <>
          <p className={styles.invalid}>{t.inbox.invalid}</p>
          <div className={styles.links}>
            <Link href="/feed">{t.inbox.goFeed}</Link>
          </div>
        </>
      ) : null}
    </div>
  );
}