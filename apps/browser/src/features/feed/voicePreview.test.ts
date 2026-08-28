import { describe, expect, it } from "vitest";
import { feedVoiceSubtitle, isOfflineTranscript } from "./voicePreview";
import type { Story } from "@/core/api/types";

function story(partial: Partial<Story>): Story {
  return {
    id: "1",
    body: "",
    topic: "other",
    pseudonym: "а",
    published_at: null,
    status: "published",
    ...partial,
  };
}

describe("isOfflineTranscript", () => {
  it("detects ru and en stubs", () => {
    expect(isOfflineTranscript("[офлайн-транскрипт: голосовое сообщение]")).toBe(
      true,
    );
    expect(isOfflineTranscript("[offline transcript: voice note]")).toBe(true);
    expect(isOfflineTranscript("Сама написала.")).toBe(false);
  });
});

describe("feedVoiceSubtitle", () => {
  it("uses typed body", () => {
    expect(
      feedVoiceSubtitle(story({ body: "текст", audio_url: "/m/a.webm" }), "Голосовое"),
    ).toBe("текст");
  });
  it("uses duration label when body is stub", () => {
    expect(
      feedVoiceSubtitle(
        story({
          body: "[офлайн-транскрипт: голосовое сообщение]",
          audio_url: "/m/a.webm",
          duration_ms: 1500,
        }),
        "Голосовое",
      ),
    ).toBe("Голосовое · 0:02");
  });
});
