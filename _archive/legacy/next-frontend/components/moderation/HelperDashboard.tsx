"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import type { ModerationDashboard as DashboardData } from "@/lib/types/api";
import { useT } from "@/lib/i18n/context";

export function HelperDashboard() {
  const t = useT();
  const [d, setD] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .moderationDashboard()
      .then(setD)
      .catch((err) => setError(err instanceof ApiError ? err.message : t.common.error));
  }, [t.common.error]);

  if (!d) return <p>{error || t.common.loading}</p>;

  const reasonLabel = (r: string) =>
    r === "abuse"
      ? t.helper.reasonAbuse
      : r === "spam"
        ? t.helper.reasonSpam
        : r === "self_harm"
          ? t.helper.reasonSelfHarm
          : t.helper.reasonOther;

  return (
    <section className="helper-dashboard">
      <h2>{t.helper.dashboardTitle}</h2>
      <p>{t.helper.dashboardLead}</p>
      <ul>
        <li>{t.helper.pendingClouds}: {d.pending_clouds}</li>
        <li>{t.helper.openReports}: {d.open_reports}</li>
        <li>{t.helper.reviewingReports}: {d.reviewing_reports}</li>
        <li>{t.helper.reports7d}: {d.reports_last_7d}</li>
      </ul>
      <h3>{t.helper.recentReports}</h3>
      {d.recent_reports.length === 0 ? (
        <p>{t.helper.noReports}</p>
      ) : (
        <ul>
          {d.recent_reports.map((r) => (
            <li key={r.id}>
              <strong>{reasonLabel(r.reason)}</strong> · {r.status}
              <p>{r.story_preview || "—"}</p>
              {r.details ? <p>{r.details}</p> : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}