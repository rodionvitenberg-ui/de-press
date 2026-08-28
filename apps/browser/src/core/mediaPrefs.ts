/**
 * Voice retention: local cache + one-shot migrate to /me/voice-retention.
 */

import type { VoiceRetention } from "@/core/api/types";

const VOICE_KEY = "depress:voice-retention";
const MIGRATED_KEY = "depress:voice-retention-migrated";

export function readVoiceRetention(): VoiceRetention {
  try {
    const v = localStorage.getItem(VOICE_KEY);
    if (v === "keep" || v === "delete_on_close") return v;
  } catch {
    /* ignore */
  }
  return "delete_on_close";
}

export function writeVoiceRetention(value: VoiceRetention): void {
  try {
    localStorage.setItem(VOICE_KEY, value);
  } catch {
    /* ignore */
  }
}

export function wasVoiceRetentionMigrated(): boolean {
  try {
    return localStorage.getItem(MIGRATED_KEY) === "1";
  } catch {
    return true;
  }
}

export function markVoiceRetentionMigrated(): void {
  try {
    localStorage.setItem(MIGRATED_KEY, "1");
  } catch {
    /* ignore */
  }
}
