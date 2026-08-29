import type { Story } from "@/core/api/types";

export function isOfflineTranscript(body: string): boolean {
  const t = body.trim();
  return t.startsWith("[офлайн") || t.startsWith("[offline");
}

export function formatDurationMs(ms: number | null | undefined): string {
  if (ms == null || !Number.isFinite(ms) || ms < 0) return "";
  const total = Math.max(0, Math.round(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function feedVoiceSubtitle(story: Story, voiceLabel: string): string {
  const body = (story.body || "").trim();
  if (story.audio_url && (!body || isOfflineTranscript(body))) {
    const clock = formatDurationMs(story.duration_ms);
    return clock ? `${voiceLabel} · ${clock}` : voiceLabel;
  }
  return body;
}
