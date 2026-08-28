/**
 * API-клиент v2 — единый origin через Vite proxy, credentials include
 * (Django session cookie SameSite=Lax).
 */

import type {
  AppNotification,
  AuthorStory,
  ChatMessage,
  Dialogue,
  DialogueRequest,
  DigestTestResponse,
  EmpathyResponse,
  FeedResponse,
  HealthResponse,
  Hearer,
  InboxOpenResponse,
  IntentOption,
  MarkAllNotificationsReadResponse,
  MarkNotificationReadResponse,
  Me,
  ModerationActionResponse,
  ModerationDashboard,
  NotifySettings,
  NotifySettingsUpdate,
  OutreachResponse,
  PulseResponse,
  QueueCloud,
  QuietPhrase,
  ReportResponse,
  SendCloudResponse,
  Story,
  SupportCloud,
  Topic,
  UnreadCountResponse,
  AiSupportResponse,
  SendCircleOptions,
  VoiceRetentionSettings,
} from "./types";

export type {
  AppNotification,
  AuthorStory,
  ChatMessage,
  ChatMessageKind,
  Dialogue,
  DialogueRequest,
  DigestTestResponse,
  EmpathyResponse,
  FeedResponse,
  HealthResponse,
  Hearer,
  InboxOpenResponse,
  IntentOption,
  MarkAllNotificationsReadResponse,
  MarkNotificationReadResponse,
  Me,
  ModerationActionResponse,
  ModerationDashboard,
  NotifySettings,
  NotifySettingsUpdate,
  OutreachResponse,
  PulseResponse,
  QueueCloud,
  QuietPhrase,
  ReportResponse,
  SendCloudResponse,
  SendCircleOptions,
  Story,
  SupportCloud,
  Topic,
  UnreadCountResponse,
  AiSupportResponse,
  VoiceRetention,
  VoiceRetentionSettings,
} from "./types";

/** Same-origin relative base (Vite proxies /api, /media, /ws → Django). */
export const API_URL = "";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = (await res.json()) as { detail?: string };
      if (data.detail) detail = data.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),

  me: () => request<Me>("/api/v1/me"),

  register: (email: string, password: string, pseudonym = "") =>
    request<Me>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, pseudonym }),
    }),

  login: (email: string, password: string) =>
    request<Me>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  /** Telegram Mini App host: raw initData query string (HMAC validated server-side). */
  loginTelegram: (initData: string) =>
    request<Me>("/api/v1/auth/telegram", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    }),

  openInbox: (token: string) =>
    request<InboxOpenResponse>("/api/v1/auth/inbox", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  logout: () =>
    request<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" }),

  topics: () => request<Topic[]>("/api/v1/topics"),

  feed: (cursor?: string | null, topic?: string | null) => {
    const params = new URLSearchParams();
    if (cursor) params.set("cursor", cursor);
    if (topic) params.set("topic", topic);
    const q = params.toString() ? `?${params}` : "";
    return request<FeedResponse>(`/api/v1/stories${q}`);
  },

  getStory: (id: string) => request<Story>(`/api/v1/stories/${id}`),

  publishStory: (body: string, opts?: { pseudonym?: string; topic?: string }) =>
    request<Story>("/api/v1/stories", {
      method: "POST",
      body: JSON.stringify({
        body,
        pseudonym: opts?.pseudonym || null,
        topic: opts?.topic || null,
      }),
    }),

  myStories: () => request<AuthorStory[]>("/api/v1/me/stories"),

  offerEmpathy: (storyId: string) =>
    request<EmpathyResponse>(`/api/v1/stories/${storyId}/empathy`, {
      method: "POST",
    }),

  setOutreachConsent: (storyId: string, outreachOptIn: boolean) =>
    request<{ ok: boolean; outreach_opt_in: boolean; message: string }>(
      `/api/v1/stories/${storyId}/empathy/outreach-consent`,
      {
        method: "POST",
        body: JSON.stringify({ outreach_opt_in: outreachOptIn }),
      },
    ),

  storyHearers: (storyId: string) =>
    request<Hearer[]>(`/api/v1/stories/${storyId}/hearers`),

  authorOutreach: (
    storyId: string,
    payload: {
      mode: "one" | "many" | "random";
      hearer_refs?: string[];
      intent?: string;
    },
  ) =>
    request<OutreachResponse>(`/api/v1/stories/${storyId}/outreach`, {
      method: "POST",
      body: JSON.stringify({
        mode: payload.mode,
        hearer_refs: payload.hearer_refs ?? [],
        intent: payload.intent ?? "listen",
      }),
    }),

  getPulse: (storyId: string) =>
    request<PulseResponse>(`/api/v1/stories/${storyId}/pulse`),

  reportStory: (storyId: string, reason: string, details = "") =>
    request<ReportResponse>(`/api/v1/stories/${storyId}/report`, {
      method: "POST",
      body: JSON.stringify({ reason, details }),
    }),

  reportMessage: (messageId: string, reason: string, details = "") =>
    request<ReportResponse>(`/api/v1/messages/${messageId}/report`, {
      method: "POST",
      body: JSON.stringify({ reason, details }),
    }),

  blockPeerInDialogue: (dialogueId: string) =>
    request<{ ok: boolean; created: boolean; message: string }>(
      `/api/v1/dialogues/${dialogueId}/block-peer`,
      { method: "POST" },
    ),

  dialogueIntents: () => request<IntentOption[]>("/api/v1/dialogue/intents"),

  requestDialogue: (storyId: string, intent: string, note = "") =>
    request<DialogueRequest>(`/api/v1/stories/${storyId}/dialogue-requests`, {
      method: "POST",
      body: JSON.stringify({ intent, note }),
    }),

  dialogueInbox: () =>
    request<DialogueRequest[]>("/api/v1/me/dialogue-requests"),

  acceptDialogueRequest: (requestId: string) =>
    request<Dialogue>(`/api/v1/dialogue-requests/${requestId}/accept`, {
      method: "POST",
    }),

  declineDialogueRequest: (requestId: string) =>
    request<DialogueRequest>(`/api/v1/dialogue-requests/${requestId}/decline`, {
      method: "POST",
    }),

  myDialogues: () => request<Dialogue[]>("/api/v1/me/dialogues"),

  dialogueMessages: (dialogueId: string) =>
    request<ChatMessage[]>(`/api/v1/dialogues/${dialogueId}/messages`),

  sendMessage: (dialogueId: string, body: string, sourceLang = "ru") =>
    request<ChatMessage>(`/api/v1/dialogues/${dialogueId}/messages`, {
      method: "POST",
      body: JSON.stringify({ body, source_lang: sourceLang }),
    }),

  sendVoiceMessage: async (
    dialogueId: string,
    blob: Blob,
    opts?: { durationMs?: number; sourceLang?: string; filename?: string },
  ) => {
    const form = new FormData();
    const name = opts?.filename || "note.webm";
    form.append("audio", blob, name);
    if (opts?.durationMs != null) {
      form.append("duration_ms", String(Math.round(opts.durationMs)));
    }
    form.append("source_lang", opts?.sourceLang || "ru");

    const res = await fetch(
      `${API_URL}/api/v1/dialogues/${dialogueId}/messages/voice`,
      {
        method: "POST",
        body: form,
        credentials: "include",
      },
    );
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = (await res.json()) as { detail?: string };
        if (data.detail) detail = data.detail;
      } catch {
        /* ignore */
      }
      throw new ApiError(detail, res.status);
    }
    return (await res.json()) as ChatMessage;
  },

  /**
   * Circle (video note) — ephemeral by design.
   * Endpoint contract ready; backend may return 404 until shipped.
   */
  sendCircleMessage: async (
    dialogueId: string,
    blob: Blob,
    opts?: SendCircleOptions,
  ) => {
    const form = new FormData();
    const name = opts?.filename || "circle.webm";
    form.append("video", blob, name);
    if (opts?.durationMs != null) {
      form.append("duration_ms", String(Math.round(opts.durationMs)));
    }
    form.append("source_lang", opts?.sourceLang || "ru");

    const res = await fetch(
      `${API_URL}/api/v1/dialogues/${dialogueId}/messages/circle`,
      {
        method: "POST",
        body: form,
        credentials: "include",
      },
    );
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = (await res.json()) as { detail?: string };
        if (data.detail) detail = data.detail;
      } catch {
        /* ignore */
      }
      if (res.status === 404 || res.status === 501 || res.status === 405) {
        throw new ApiError(
          "Circles API is not enabled on the server yet",
          res.status,
        );
      }
      throw new ApiError(detail, res.status);
    }
    return (await res.json()) as ChatMessage;
  },

  /**
   * Voice retention settings (Ephemeral Voice Note).
   * GET/POST planned; until backend exists, throws 404 and callers use local prefs.
   */
  voiceRetentionSettings: () =>
    request<VoiceRetentionSettings>("/api/v1/me/voice-retention"),

  updateVoiceRetentionSettings: (payload: VoiceRetentionSettings) =>
    request<VoiceRetentionSettings>("/api/v1/me/voice-retention", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  translateMessage: (messageId: string, targetLang: string) =>
    request<ChatMessage>(`/api/v1/messages/${messageId}/translate`, {
      method: "POST",
      body: JSON.stringify({ target_lang: targetLang }),
    }),

  transcribeMessage: (messageId: string) =>
    request<ChatMessage>(`/api/v1/messages/${messageId}/transcribe`, {
      method: "POST",
    }),

  closeDialogue: (dialogueId: string) =>
    request<Dialogue>(`/api/v1/dialogues/${dialogueId}/close`, {
      method: "POST",
    }),

  aiSupport: (
    messages: { role: string; content: string }[],
    surface: "companion" | "anti_panic" = "companion",
  ) =>
    request<AiSupportResponse>("/api/v1/ai/support", {
      method: "POST",
      body: JSON.stringify({ messages, surface }),
    }),

  quietPhrases: (lang: "ru" | "en" = "ru") =>
    request<QuietPhrase[]>(`/api/v1/quiet-phrases?lang=${lang}`),

  sendQuietPhrase: (storyId: string, phraseKey: string) =>
    request<SendCloudResponse>(`/api/v1/stories/${storyId}/clouds`, {
      method: "POST",
      body: JSON.stringify({ phrase_key: phraseKey }),
    }),

  sendModeratedCloud: (storyId: string, body: string) =>
    request<SendCloudResponse>(`/api/v1/stories/${storyId}/clouds`, {
      method: "POST",
      body: JSON.stringify({ body }),
    }),

  storyClouds: (storyId: string) =>
    request<SupportCloud[]>(`/api/v1/stories/${storyId}/clouds`),

  moderationQueue: () => request<QueueCloud[]>("/api/v1/moderation/clouds"),

  approveCloud: (cloudId: string) =>
    request<ModerationActionResponse>(
      `/api/v1/moderation/clouds/${cloudId}/approve`,
      { method: "POST" },
    ),

  rejectCloud: (cloudId: string) =>
    request<ModerationActionResponse>(
      `/api/v1/moderation/clouds/${cloudId}/reject`,
      { method: "POST" },
    ),

  moderationDashboard: () =>
    request<ModerationDashboard>("/api/v1/moderation/dashboard"),

  notifications: (limit = 30) =>
    request<AppNotification[]>(`/api/v1/me/notifications?limit=${limit}`),

  notificationsUnreadCount: () =>
    request<UnreadCountResponse>("/api/v1/me/notifications/unread-count"),

  markNotificationRead: (notificationId: string) =>
    request<MarkNotificationReadResponse>(
      `/api/v1/me/notifications/${notificationId}/read`,
      { method: "POST" },
    ),

  markAllNotificationsRead: () =>
    request<MarkAllNotificationsReadResponse>(
      "/api/v1/me/notifications/read-all",
      { method: "POST" },
    ),

  notifySettings: () => request<NotifySettings>("/api/v1/me/notify-settings"),

  updateNotifySettings: (payload: NotifySettingsUpdate) =>
    request<NotifySettings>("/api/v1/me/notify-settings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  testNotifyDigest: () =>
    request<DigestTestResponse>("/api/v1/me/notify-settings/test", {
      method: "POST",
    }),

  testTelegramDigest: () =>
    request<DigestTestResponse>("/api/v1/me/notify-settings/test-telegram", {
      method: "POST",
    }),
};
