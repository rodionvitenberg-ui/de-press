/**
 * Smoke tests for start_param → route mapping (audit Q4). Pure logic:
 * prefix forms, UUID normalization, catalog words, unknown params.
 */
import { describe, expect, it } from "vitest";
import { resolveStartParam } from "./startParam";

describe("resolveStartParam()", () => {
  it("maps catalog words", () => {
    expect(resolveStartParam("feed")?.path).toBe("/feed");
    expect(resolveStartParam("FEED")?.path).toBe("/feed");
    expect(resolveStartParam("n")?.path).toBe("/feed");
    expect(resolveStartParam("write")?.path).toBe("/feed/new");
    expect(resolveStartParam("chats")?.path).toBe("/chat");
    expect(resolveStartParam("mood")?.path).toBe("/patterns");
    expect(resolveStartParam("wait")?.path).toBe("/help/wait");
    expect(resolveStartParam("help_ai")?.path).toBe("/help/ai");
    expect(resolveStartParam("helpers")?.path).toBe("/helper");
  });

  it("maps deep-link story ids, normalizing compact UUIDs", () => {
    const target = resolveStartParam("s_7c9e6679741f4bf7bb8f2a5f7a4d3b21");
    expect(target?.path).toBe("/feed/7c9e6679-741f-4bf7-bb8f-2a5f7a4d3b21");
    expect(
      resolveStartParam("story_7c9e6679-741f-4bf7-bb8f-2a5f7a4d3b21")?.path,
    ).toBe("/feed/7c9e6679-741f-4bf7-bb8f-2a5f7a4d3b21");
    expect(
      resolveStartParam("d_7c9e6679-741f-4bf7-bb8f-2a5f7a4d3b21")?.path,
    ).toBe("/chat/7c9e6679-741f-4bf7-bb8f-2a5f7a4d3b21");
  });

  it("maps one-time helper invites to the join route", () => {
    expect(resolveStartParam("helper_join-7c9e6679741f4bf7bb8f2a5f7a4d3b21"))
      .toEqual({
        path: "/helper/join?token=7c9e6679-741f-4bf7-bb8f-2a5f7a4d3b21",
        param: "helper_join-7c9e6679741f4bf7bb8f2a5f7a4d3b21",
      });
  });

  it("flags anti-panic entry for quiet phrases", () => {
    const target = resolveStartParam("meh");
    expect(target?.path).toBe("/help");
    expect(target?.enterAntiPanic).toBe(true);
  });

  it("returns null for empty, invalid, or unknown params", () => {
    expect(resolveStartParam("")).toBeNull();
    expect(resolveStartParam("story_not-a-uuid")).toBeNull();
    expect(resolveStartParam("banana")).toBeNull();
  });
});
