"use client";

import { useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { useI18n } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { TextArea } from "@/components/ui/TextArea";
import styles from "./ReportButton.module.css";

interface ReportButtonProps {
  storyId: string;
}

export function ReportButton({ storyId }: ReportButtonProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<string>("abuse");
  const [details, setDetails] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const reasons = useMemo(
    () => [
      { value: "abuse", label: t.report.reasonsAbuse },
      { value: "spam", label: t.report.reasonsSpam },
      { value: "self_harm", label: t.report.reasonsSelfHarm },
      { value: "other", label: t.report.reasonsOther },
    ],
    [t],
  );

  async function submit() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await api.reportStory(storyId, reason, details);
      setMessage(res.message);
      setOpen(false);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.wrap}>
      {!open ? (
        <Button variant="ghost" onClick={() => setOpen(true)}>
          {t.report.report}
        </Button>
      ) : (
        <div className={styles.panel}>
          <label className={styles.label} htmlFor={`reason-${storyId}`}>
            {t.report.why}
          </label>
          <select
            id={`reason-${storyId}`}
            className={styles.select}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          >
            {reasons.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
          <TextArea
            id={`details-${storyId}`}
            label={t.report.details}
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            rows={3}
          />
          <div className={styles.actions}>
            <Button onClick={submit} disabled={loading}>
              {t.report.send}
            </Button>
            <Button variant="ghost" onClick={() => setOpen(false)} disabled={loading}>
              {t.report.cancel}
            </Button>
          </div>
        </div>
      )}
      {message ? <p className={styles.msg}>{message}</p> : null}
    </div>
  );
}
