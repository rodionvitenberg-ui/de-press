"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { NotifySettings as NotifySettingsData } from "@/lib/types/api";
import { useT } from "@/lib/i18n/context";

export function NotifySettings() {
  const t = useT();
  const [s, setS] = useState<NotifySettingsData | null>(null);
  const [email, setEmail] = useState("");
  const [optIn, setOptIn] = useState(false);
  const [freq, setFreq] = useState<"off" | "immediate" | "daily">("daily");
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .notifySettings()
      .then((d) => {
        setS(d);
        setEmail(d.email || "");
        setOptIn(d.notify_email_opt_in);
        setFreq(d.notify_digest_frequency);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : t.common.error));
  }, [t.common.error]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setHint(null);
    try {
      const d = await api.updateNotifySettings({
        notify_email_opt_in: optIn,
        notify_digest_frequency: freq,
        contact_email: email,
      });
      setS(d);
      setHint(t.notify.saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setBusy(false);
    }
  }

  async function test() {
    setBusy(true);
    setError(null);
    setHint(null);
    try {
      const d = await api.testNotifyDigest();
      setHint(d.message || t.notify.testSent);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setBusy(false);
    }
  }

  if (!s) return <p>{error || t.common.loading}</p>;

  return (
    <form className="profile-notify" onSubmit={save}>
      <h2>{t.notify.title}</h2>
      <p>{t.notify.lead}</p>
      {!s.email ? (
        <div>
          <label>{t.notify.emailLabel}</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t.notify.emailPlaceholder}
          />
          <p>{t.notify.emailHelp}</p>
        </div>
      ) : (
        <p>{s.email}</p>
      )}
      <label>
        <input type="checkbox" checked={optIn} onChange={(e) => setOptIn(e.target.checked)} />
        {t.notify.optIn}
      </label>
      <label>{t.notify.frequency}</label>
      <select value={freq} onChange={(e) => setFreq(e.target.value as typeof freq)}>
        <option value="off">{t.notify.freqOff}</option>
        <option value="immediate">{t.notify.freqImmediate}</option>
        <option value="daily">{t.notify.freqDaily}</option>
      </select>
      {error ? <p>{error}</p> : null}
      {hint ? <p>{hint}</p> : null}
      <div>
        <button type="submit" disabled={busy}>{t.common.save}</button>
        <button type="button" disabled={busy} onClick={test}>{t.notify.testDigest}</button>
      </div>
    </form>
  );
}