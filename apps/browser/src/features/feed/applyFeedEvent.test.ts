import { describe, expect, it } from "vitest";
import {
  applyFeedEvent,
  flattenFeed,
  isMine,
  type FeedInfinite,
} from "./applyFeedEvent";
import type { Me, Story } from "@/core/api/types";

function story(id: string, extra: Partial<Story> = {}): Story {
  return {
    id,
    body: `b-${id}`,
    topic: "other",
    pseudonym: "anon",
    published_at: null,
    status: "published",
    ...extra,
  };
}

const accountMe: Me = {
  kind: "account",
  email: "e@x.io",
  account_id: "a1",
  session_id: null,
  pseudonym: "p",
  is_authenticated: true,
};

const sessionMe: Me = {
  kind: "anonymous",
  email: null,
  account_id: null,
  session_id: "s1",
  pseudonym: "p",
  is_authenticated: false,
};

function feed(...ids: string[]): FeedInfinite {
  return {
    pages: [{ items: ids.map((id) => story(id)), next_cursor: null }],
    pageParams: [null],
  };
}

const idsOf = (data?: FeedInfinite): string[] =>
  data ? data.pages.flatMap((page) => page.items.map((s) => s.id)) : [];

describe("isMine", () => {
  it("trusts the server flag first", () => {
    expect(isMine(story("1", { is_mine: true }), null)).toBe(true);
    expect(isMine(story("1", { is_mine: false }), accountMe)).toBe(false);
  });

  it("matches account author_key", () => {
    const s = story("1", { author_key: "a:a1" });
    expect(isMine(s, accountMe)).toBe(true);
    expect(isMine(s, sessionMe)).toBe(false);
  });

  it("matches anonymous session author_key", () => {
    const s = story("1", { author_key: "s:s1" });
    expect(isMine(s, sessionMe)).toBe(true);
    expect(isMine(s, accountMe)).toBe(false);
  });

  it("is false without a key or without me", () => {
    expect(isMine(story("1"), accountMe)).toBe(false);
    expect(isMine(story("1", { author_key: "a:a1" }), null)).toBe(false);
  });
});

describe("flattenFeed", () => {
  it("concatenates pages and dedupes by id", () => {
    const data = {
      pages: [
        { items: [story("1"), story("2")], next_cursor: "c" },
        { items: [story("2"), story("3")], next_cursor: null },
      ],
    };
    expect(flattenFeed(data).map((s) => s.id)).toEqual(["1", "2", "3"]);
  });

  it("returns [] for undefined", () => {
    expect(flattenFeed(undefined)).toEqual([]);
  });
});

describe("applyFeedEvent", () => {
  it("story.published prepends and dedupes; creates feed from nothing", () => {
    const ev = { type: "story.published" as const, story: story("new") };
    const next = applyFeedEvent(feed("1", "2"), ev, accountMe);
    expect(idsOf(next)).toEqual(["new", "1", "2"]);

    const fromEmpty = applyFeedEvent(undefined, ev, accountMe);
    expect(idsOf(fromEmpty)).toEqual(["new"]);

    const dupe = applyFeedEvent(feed("new", "1"), ev, accountMe);
    expect(idsOf(dupe)).toEqual(["new", "1"]);
  });

  it("story.published tags authorship for me", () => {
    const ev = {
      type: "story.published" as const,
      story: story("n", { author_key: "a:a1" }),
    };
    const next = applyFeedEvent(undefined, ev, accountMe);
    expect(next?.pages[0].items[0].is_mine).toBe(true);
  });

  it("story.updated replaces in place", () => {
    const ev = {
      type: "story.updated" as const,
      story: story("2", { body: "edited" }),
    };
    const next = applyFeedEvent(feed("1", "2", "3"), ev, accountMe);
    expect(idsOf(next)).toEqual(["1", "2", "3"]);
    expect(next?.pages[0].items[1].body).toBe("edited");
  });

  it("story.hidden removes someone else's row, keeps mine in place", () => {
    const theirs = applyFeedEvent(
      feed("1", "2"),
      { type: "story.hidden", story: story("1", { author_key: "a:x" }) },
      accountMe,
    );
    expect(idsOf(theirs)).toEqual(["2"]);

    const mine = applyFeedEvent(
      feed("1", "2"),
      {
        type: "story.hidden",
        story: story("1", { body: "hidden-mine", author_key: "a:a1" }),
      },
      accountMe,
    );
    expect(idsOf(mine)).toEqual(["1", "2"]);
    expect(mine?.pages[0].items[0].status).toBe("published");
  });

  it("story.unhidden prepends back", () => {
    const ev = {
      type: "story.unhidden" as const,
      story: story("9", { author_key: "a:a1" }),
    };
    const next = applyFeedEvent(feed("1"), ev, accountMe);
    expect(idsOf(next)).toEqual(["9", "1"]);
  });

  it("story.deleted drops only that id", () => {
    const next = applyFeedEvent(
      feed("1", "2", "3"),
      { type: "story.deleted", story_id: "2" },
      accountMe,
    );
    expect(idsOf(next)).toEqual(["1", "3"]);
  });

  it("story.commented bumps the post to the top once", () => {
    const post = story("2");
    const next = applyFeedEvent(
      feed("1", "2", "3"),
      { type: "story.commented", story: post, post_id: "2" },
      accountMe,
    );
    expect(idsOf(next)).toEqual(["2", "1", "3"]);
  });

  it("mineOnly ignores other people's stories", () => {
    const ev = {
      type: "story.published" as const,
      story: story("x", { author_key: "a:other" }),
    };
    const next = applyFeedEvent(feed("1"), ev, accountMe, { mineOnly: true });
    expect(idsOf(next)).toEqual(["1"]);
  });
});
