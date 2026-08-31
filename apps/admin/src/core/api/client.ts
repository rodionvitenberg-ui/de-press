/**
 * API-клиент админки — единый origin через Vite proxy, credentials include
 * (Django session cookie). 401/403 → экран «нужен staff-доступ».
 */

import type {
  AdminOverview,
  ModerationActionLog,
  ResolveBody,
  ResolveResponse,
  AdminReport,
} from "./types";

export type { AdminOverview, AdminReport, ModerationActionLog };

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const data = (await res.json()) as { detail?: unknown; message?: unknown };
      if (typeof data?.detail === "string") message = data.detail;
      else if (typeof data?.message === "string") message = data.message;
    } catch {
      // не JSON — оставляем «HTTP <code>»
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as T;
}

export const api = {
  overview: () => request<AdminOverview>("/admin/overview"),
  reports: (status: string) =>
    request<AdminReport[]>(`/admin/reports?status=${encodeURIComponent(status)}`),
  resolveReport: (id: string, body: ResolveBody) =>
    request<ResolveResponse>(`/admin/reports/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  moderationLog: () =>
    request<ModerationActionLog[]>("/admin/moderation-log?limit=100"),
};
