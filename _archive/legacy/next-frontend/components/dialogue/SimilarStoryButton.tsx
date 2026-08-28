"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { IntentOption } from "@/lib/types/api";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextArea";
import styles from "./SimilarStoryButton.module.css";

interface Props {
  storyId: string;
}

export function SimilarStoryButton({ storyId }: Props) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [intents, setIntents] = useState<IntentOption[]>([]);
  const [intent, setIntent] = useState("share");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void api.dialogueIntents().then(setIntents).catch(() => setIntents([]));
  }, []);

  async function submit() {
    setLoading(true);
    setMsg(null);
    try {
      await api.requestDialogue(storyId, intent, note);
      setMsg(t.dialogue.requestSent);
      setOpen(false);
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.wrap}>
      {!open ? (
        <Button variant="secondary" onClick={() => setOpen(true)}>
          {t.dialogue.similar}
        </Button>
      ) : (
        <div className={styles.panel}>
          <p className={styles.hint}>{t.dialogue.similarHint}</p>
          <select
            className={styles.select}
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
          >
            {intents.map((i) => (
              <option key={i.value} value={i.value}>
                {i.label}
              </option>
            ))}
          </select>
          <TextInput
            id={`note-${storyId}`}
            label={t.dialogue.noteLabel}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={280}
            placeholder={t.dialogue.notePlaceholder}
          />
          <div className={styles.actions}>
            <Button onClick={submit} disabled={loading}>
              {t.dialogue.sendRequest}
            </Button>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              {t.dialogue.cancel}
            </Button>
          </div>
        </div>
      )}
      {msg ? <p className={styles.msg}>{msg}</p> : null}
    </div>
  );
}
