/**
 * Client-side media preferences until server settings land.
 * Voice retention: Ephemeral Voice Note (CONTEXT.md).
 */

import type { VoiceRetention } from "@/core/api/types";

const VOICE_KEY = "depress:voice-retention";

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
