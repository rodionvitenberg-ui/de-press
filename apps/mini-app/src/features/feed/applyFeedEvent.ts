import type { FeedResponse, Me, Story } from "@/core/api/types";

export type FeedInfinite = {
  pages: FeedResponse[];
  pageParams: (string | null)[];
};

export type FeedEvent =
  | { type: "story.published"; story: Story }
  | { type: "story.updated"; story: Story }
  | { type: "story.hidden"; story: Story }
  | { type: "story.unhidden"; story: Story }
  | { type: "story.deleted"; story_id: string; author_key?: string }
  | { type: "story.commented"; story: Story; post_id: string };

export function isMine(
  story: Pick<Story, "author_key" | "is_mine">,
  me: Me | null | undefined,
): boolean {
  if (story.is_mine) return true;
  const key = story.author_key;
  if (!key || !me) return false;
  if (me.account_id && key === `a:${me.account_id}`) return true;
  if (me.session_id && key === `s:${me.session_id}`) return true;
  return false;
}

export function flattenFeed(
  data: { pages: Array<{ items: Story[] }> } | undefined,
): Story[] {
  const seen = new Set<string>();
  const out: Story[] = [];
  for (const page of data?.pages ?? []) {
    for (const story of page.items) {
      if (seen.has(story.id)) continue;
      seen.add(story.id);
      out.push(story);
    }
  }
  return out;
}

function mapPages(
  data: FeedInfinite,
  mapper: (items: Story[]) => Story[],
): FeedInfinite {
  return {
    ...data,
    pages: data.pages.map((page) => ({ ...page, items: mapper(page.items) })),
  };
}

function emptyFeed(story: Story): FeedInfinite {
  return {
    pages: [{ items: [story], next_cursor: null }],
    pageParams: [null],
  };
}

function tagged(story: Story, me: Me | null | undefined): Story {
  return { ...story, is_mine: isMine(story, me) };
}

function dropMatching(items: Story[], pred: (s: Story) => boolean): Story[] {
  return items.filter((s) => !pred(s));
}

function prependFirst(data: FeedInfinite, story: Story): FeedInfinite {
  if (!data.pages.length) return emptyFeed(story);
  const [first, ...rest] = data.pages;
  return {
    ...data,
    pages: [{ ...first, items: [story, ...first.items] }, ...rest],
  };
}

export function applyFeedEvent(
  data: FeedInfinite | undefined,
  event: FeedEvent,
  me: Me | null | undefined,
  opts?: { mineOnly?: boolean },
): FeedInfinite | undefined {
  const mineOnly = Boolean(opts?.mineOnly);

  if (event.type === "story.deleted") {
    if (!data) return data;
    return mapPages(data, (items) =>
      dropMatching(items, (s) => s.id === event.story_id),
    );
  }

  if (event.type === "story.commented") {
    if (!data) return data;
    const postId = event.post_id;
    let post: Story | undefined;
    for (const page of data.pages) {
      post = page.items.find((s) => s.id === postId);
      if (post) break;
    }
    if (!post) return data;
    const stripped = mapPages(data, (items) =>
      dropMatching(items, (s) => s.id === postId),
    );
    return prependFirst(stripped, post);
  }

  const story = tagged(event.story, me);
  if (mineOnly && !isMine(story, me)) {
    return data;
  }

  if (event.type === "story.updated") {
    if (!data) return data;
    return mapPages(data, (items) =>
      items.map((s) => (s.id === story.id ? { ...s, ...story } : s)),
    );
  }

  if (event.type === "story.hidden") {
    if (!data) return data;
    if (isMine(story, me) || mineOnly) {
      return mapPages(data, (items) =>
        items.map((s) => (s.id === story.id ? { ...s, ...story } : s)),
      );
    }
    return mapPages(data, (items) =>
      dropMatching(items, (s) => s.id === story.id),
    );
  }

  if (event.type === "story.published" || event.type === "story.unhidden") {
    const next = data ?? emptyFeed(story);
    const stripped = mapPages(next, (items) =>
      dropMatching(items, (s) => s.id === story.id),
    );
    return prependFirst(stripped, story);
  }

  return data;
}
