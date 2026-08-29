/** API response types — ported from legacy Next for app v2. */

export interface Me {
  kind: "account" | "anonymous";
  email: string | null;
  account_id: string | null;
  session_id: string | null;
  pseudonym: string;
  is_authenticated: boolean;
  is_helper?: boolean;
  is_staff?: boolean;
  is_on_duty?: boolean;
  helper_org?: string;
  helper_badge?: string;
}

/** Presence booleans only — no counts, no names (A6). */
export interface HelpPresence {
  someone_on_duty: boolean;
  someone_online: boolean;
}

/** One-time Helper invite (A3). */
export interface HelperInvite {
  token: string;
  org: string;
  expires_at: string;
  used: boolean;
}

export interface Story {
  id: string;
  body: string;
  topic: string;
  pseudonym: string;
  published_at: string | null;
  status: string;
}

export interface AuthorStory extends Story {
  pulse_count: number;
  pulse_message: string;
}

export interface Topic {
  value: string;
  label: string;
}

export interface FeedResponse {
  items: Story[];
  next_cursor: string | null;
}

export interface EmpathyResponse {
  ok: boolean;
  created: boolean;
  message: string;
  outreach_opt_in?: boolean;
}

export interface Hearer {
  hearer_ref: string;
  pseudonym: string;
  outreach_opt_in: boolean;
  created_at: string;
  has_open_dialogue: boolean;
}

export interface OutreachResponse {
  ok: boolean;
  created_count: number;
  reused_count: number;
  dialogues: Dialogue[];
  message: string;
}

export interface PulseResponse {
  story_id: string;
  count: number;
  message: string;
}

export interface HealthResponse {
  status: string;
  database: boolean;
  redis: boolean;
  channels?: boolean;
}

export interface ReportResponse {
  ok: boolean;
  created: boolean;
  report_id: string;
  message: string;
}

export interface DialogueRequest {
  id: string;
  story_id: string;
  intent: string;
  note: string;
  status: string;
  created_at: string;
}

export interface Dialogue {
  id: string;
  story_id: string;
  intent: string;
  status: string;
  source?: string;
  rules: string;
  updated_at: string;
}

/** Message kinds in Initiated Dialogue. `circle` = short ephemeral video. */
export type ChatMessageKind = "text" | "voice" | "circle" | string;

export interface ChatMessage {
  id: string;
  kind?: ChatMessageKind;
  body: string;
  display_text?: string;
  transcript?: string;
  source_lang?: string;
  translations?: Record<string, string>;
  duration_ms?: number | null;
  audio_url?: string | null;
  /** Circle / future video media (same-origin path or absolute URL). */
  video_url?: string | null;
  /** Ephemeral: deleted when dialogue closes (Circles always true when set). */
  ephemeral?: boolean;
  created_at: string;
  from_me: boolean;
  is_system: boolean;
  from_account_id?: string | null;
  from_session_id?: string | null;
}

/**
 * Voice note lifetime preference (Ephemeral Voice Note).
 * Server will honor later; client stores preference now.
 */
export type VoiceRetention = "delete_on_close" | "keep";

export interface VoiceRetentionSettings {
  voice_retention: VoiceRetention;
}

/**
 * Planned circle upload contract (backend not shipped yet):
 * POST /api/v1/dialogues/{id}/messages/circle
 * multipart: video (file), duration_ms?, source_lang?
 * → ChatMessage with kind=circle, video_url, ephemeral=true
 */
export interface SendCircleOptions {
  durationMs?: number;
  sourceLang?: string;
  filename?: string;
}

export interface IntentOption {
  value: string;
  label: string;
}

export interface QuietPhrase {
  key: string;
  text: string;
}

export interface SendCloudResponse {
  ok: boolean;
  created: boolean;
  message: string;
  cloud_id: string | null;
  status?: string | null;
}

export interface SupportCloud {
  id: string;
  body: string;
  kind: string;
  status: string;
  pseudonym: string;
  sender_ref: string;
  helper_badge?: string;
  is_priority?: boolean;
  created_at: string;
}

export interface QueueCloud extends SupportCloud {
  story_id: string;
  story_preview: string;
}

export interface ModerationActionResponse {
  ok: boolean;
  status: string;
  message: string;
  cloud_id: string;
}

export type NotificationKind =
  | "dialogue_request"
  | "dialogue_request_review"
  | "support_cloud"
  | "cloud_approved"
  | "dialogue_opened"
  | "outreach_intro"
  | "message";

export interface AppNotification {
  id: string;
  kind: NotificationKind;
  payload: Record<string, string>;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCountResponse {
  count: number;
}

export interface MarkNotificationReadResponse {
  ok: boolean;
  id: string;
  is_read: boolean;
}

export interface MarkAllNotificationsReadResponse {
  ok: boolean;
  updated: number;
}

export interface InboxOpenResponse {
  ok: boolean;
  kind: "account" | "anonymous";
  opened: number;
}

export interface NotifySettings {
  ok: boolean;
  email: string;
  notify_email_opt_in: boolean;
  notify_digest_frequency: "off" | "immediate" | "daily";
  email_verified: boolean;
  has_telegram?: boolean;
  notify_telegram_opt_in?: boolean;
}

export interface NotifySettingsUpdate {
  notify_email_opt_in?: boolean;
  notify_digest_frequency?: "off" | "immediate" | "daily";
  contact_email?: string;
  notify_telegram_opt_in?: boolean;
}

export interface DigestTestResponse {
  ok: boolean;
  sent_to: string;
  message: string;
}

export interface ModerationDashboard {
  pending_clouds: number;
  open_reports: number;
  reviewing_reports: number;
  reports_last_7d: number;
  recent_reports: {
    id: string;
    reason: string;
    status: string;
    story_preview: string;
    details: string;
    created_at: string;
  }[];
}

export interface AiSupportResponse {
  reply: string;
  crisis: boolean;
  offline: boolean;
  labeled_ai: boolean;
  disclaimer: string;
}

export interface HelpRequest {
  id: string;
  note: string;
  status: "pending" | "accepted" | "cancelled" | string;
  dialogue_id: string | null;
  created_at: string;
}
