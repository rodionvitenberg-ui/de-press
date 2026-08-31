import { useQuery } from "@tanstack/react-query";

import { api } from "../core/api/client";
import { useI18n } from "../core/i18n/context";

export function ModerationLog({ onError }: { onError: (e: unknown) => void }) {
  const { t } = useI18n();
  const query = useQuery({
    queryKey: ["admin-log"],
    queryFn: () => api.moderationLog(),
    retry: false,
  });

  if (query.isError) {
    onError(query.error);
    return <p className="empty">{t.common.error} — {String(query.error)}</p>;
  }
  if (query.isLoading) {
    return <p className="empty">{t.common.loading}</p>;
  }
  const rows = query.data ?? [];
  if (rows.length === 0) {
    return <p className="empty">{t.log.empty}</p>;
  }

  return (
    <section>
      <table className="log">
        <thead>
          <tr>
            <th>{t.log.when}</th>
            <th>{t.log.action}</th>
            <th>{t.log.reason}</th>
            <th>{t.log.note}</th>
            <th>{t.log.actor}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id}>
              <td>{new Date(a.created_at).toLocaleString()}</td>
              <td>{t.actions[a.action as keyof typeof t.actions] ?? a.action}</td>
              <td>{a.reason ? (t.reasons[a.reason as keyof typeof t.reasons] ?? a.reason) : "—"}</td>
              <td>{a.note || "—"}</td>
              <td>{a.actor_email || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
