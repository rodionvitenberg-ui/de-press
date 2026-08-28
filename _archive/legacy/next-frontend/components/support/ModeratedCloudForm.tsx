"use client";

import { useState, type FormEvent } from "react";
import { api, ApiError } from "@/lib/api/client";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { TextArea } from "@/components/ui/TextArea";
import styles from "./ModeratedCloudForm.module.css";

interface ModeratedCloudFormProps {
  storyId: string;
}

const MAX = 280;

export function ModeratedCloudForm({ storyId }: ModeratedCloudFormProps) {
  const t = useT();
  const [body, setBody] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = body.trim();
    if (!text) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await api.sendModeratedCloud(storyId, text);
      setMessage(res.message);
      if (res.created) setBody("");
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <h3 className={styles.title}>{t.support.freeTitle}</h3>
      <p className={styles.lead}>{t.support.freeLead}</p>
      <TextArea
        id={`cloud-body-${storyId}`}
        label={t.support.freeLabel}
        value={body}
        maxLength={MAX}
        rows={3}
        onChange={(e) => setBody(e.target.value)}
        placeholder={t.support.freePlaceholder}
      />
      <div className={styles.row}>
        <span className={styles.counter}>
          {body.trim().length}/{MAX}
        </span>
        <Button type="submit" variant="secondary" disabled={loading || !body.trim()}>
          {t.support.freeSubmit}
        </Button>
      </div>
      {message ? <p className={styles.hint}>{message}</p> : null}
    </form>
  );
}
