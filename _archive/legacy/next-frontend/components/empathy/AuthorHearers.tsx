"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { Hearer } from "@/lib/types/api";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import styles from "./AuthorHearers.module.css";

interface AuthorHearersProps {
  storyId: string;
}

export function AuthorHearers({ storyId }: AuthorHearersProps) {
  const router = useRouter();
  const t = useT();
  const [open, setOpen] = useState(false);
  const [hearers, setHearers] = useState<Hearer[] | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const list = await api.storyHearers(storyId);
      setHearers(list);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setHearers(null);
        return;
      }
      setError(err instanceof ApiError ? err.message : t.common.error);
      setHearers([]);
    }
  }, [storyId, t.common.error]);

  useEffect(() => {
    if (open && hearers === null && !error) {
      void load();
    }
  }, [open, hearers, error, load]);

  function toggle(ref: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(ref)) next.delete(ref);
      else next.add(ref);
      return next;
    });
  }

  async function outreach(
    mode: "one" | "many" | "random",
    refs?: string[],
  ) {
    setBusy(true);
    setHint(null);
    setError(null);
    try {
      const res = await api.authorOutreach(storyId, {
        mode,
        hearer_refs: refs,
      });
      setHint(res.message);
      await load();
      if (res.dialogues.length === 1) {
        router.push(`/dialogues/${res.dialogues[0].id}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setBusy(false);
    }
  }

  const eligible = hearers?.filter((h) => h.outreach_opt_in) ?? [];

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.toggle}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {open ? t.hearers.hide : t.hearers.show}
      </button>

      {open ? (
        <div className={styles.panel}>
          <p className={styles.lead}>{t.hearers.lead}</p>

          {error ? <p className={styles.error}>{error}</p> : null}
          {hint ? <p className={styles.hint}>{hint}</p> : null}

          {hearers === null && !error ? (
            <p className={styles.meta}>{t.hearers.loading}</p>
          ) : null}

          {hearers && hearers.length === 0 ? (
            <p className={styles.meta}>{t.hearers.empty}</p>
          ) : null}

          {hearers && hearers.length > 0 ? (
            <>
              <ul className={styles.list}>
                {hearers.map((h) => (
                  <li key={h.hearer_ref} className={styles.row}>
                    <label className={styles.label}>
                      <input
                        type="checkbox"
                        checked={selected.has(h.hearer_ref)}
                        disabled={!h.outreach_opt_in || busy}
                        onChange={() => toggle(h.hearer_ref)}
                      />
                      <span className={styles.name}>{h.pseudonym}</span>
                    </label>
                    <span className={styles.meta}>
                      {!h.outreach_opt_in
                        ? t.hearers.outreachOff
                        : h.has_open_dialogue
                          ? t.hearers.openDialogue
                          : t.hearers.canWrite}
                    </span>
                    <Button
                      variant="ghost"
                      disabled={!h.outreach_opt_in || busy}
                      onClick={() => outreach("one", [h.hearer_ref])}
                    >
                      {h.has_open_dialogue ? t.hearers.toChat : t.hearers.write}
                    </Button>
                  </li>
                ))}
              </ul>

              <div className={styles.actions}>
                <Button
                  variant="secondary"
                  disabled={busy || eligible.length === 0}
                  onClick={() => outreach("random")}
                >
                  {t.hearers.random}
                </Button>
                <Button
                  disabled={busy || selected.size === 0}
                  onClick={() =>
                    outreach(
                      selected.size === 1 ? "one" : "many",
                      Array.from(selected),
                    )
                  }
                >
                  {t.hearers.selected} ({selected.size})
                </Button>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
