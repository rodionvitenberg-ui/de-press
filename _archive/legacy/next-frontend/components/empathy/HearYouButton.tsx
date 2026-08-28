"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { useT } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import styles from "./HearYouButton.module.css";

interface HearYouButtonProps {
  storyId: string;
}

export function HearYouButton({ storyId }: HearYouButtonProps) {
  const t = useT();
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [offered, setOffered] = useState(false);
  const [optIn, setOptIn] = useState(true);
  const [consentBusy, setConsentBusy] = useState(false);

  async function onClick() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await api.offerEmpathy(storyId);
      setMessage(res.message);
      setOffered(true);
      setOptIn(res.outreach_opt_in ?? true);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  }

  async function onConsentChange(next: boolean) {
    setConsentBusy(true);
    try {
      const res = await api.setOutreachConsent(storyId, next);
      setOptIn(res.outreach_opt_in);
      setMessage(res.message);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setConsentBusy(false);
    }
  }

  return (
    <div className={styles.wrap}>
      <Button variant="secondary" onClick={onClick} disabled={loading}>
        {t.empathy.hearYou}
      </Button>
      {message ? <p className={styles.hint}>{message}</p> : null}
      {offered ? (
        <label className={styles.consent}>
          <input
            type="checkbox"
            checked={optIn}
            disabled={consentBusy}
            onChange={(e) => void onConsentChange(e.target.checked)}
          />
          <span>{t.empathy.consent}</span>
        </label>
      ) : null}
    </div>
  );
}
