import { useMemo, useRef, useState } from "react";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Link, useParams } from "react-router-dom";
import { api } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import { ListRow } from "@/components/tg/ListRow";
import styles from "./FeedList.module.css";

const ROW_ESTIMATE = 72;
const VIRTUAL_THRESHOLD = 24;

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  const mins = Math.floor((Date.now() - then) / 60_000);
  if (mins < 1) return "";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

export function FeedList() {
  const { id: activeId } = useParams<{ id?: string }>();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const query = useInfiniteQuery({
    queryKey: ["feed"],
    queryFn: ({ pageParam }) => api.feed(pageParam ?? null, null),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
  });

  const stories = useMemo(() => {
    const all = query.data?.pages.flatMap((p) => p.items) ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return all;
    return all.filter(
      (s) =>
        s.body.toLowerCase().includes(needle) ||
        s.pseudonym.toLowerCase().includes(needle) ||
        s.topic.toLowerCase().includes(needle),
    );
  }, [query.data, q]);

  const useVirtual = stories.length >= VIRTUAL_THRESHOLD;

  const virtualizer = useVirtualizer({
    count: useVirtual ? stories.length : 0,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_ESTIMATE,
    overscan: 8,
  });

  function prefetchStory(id: string) {
    void queryClient.prefetchQuery({
      queryKey: ["story", id],
      queryFn: () => api.getStory(id),
      staleTime: 30_000,
    });
  }

  return (
    <div className={styles.list}>
      <div className={styles.searchWrap}>
        <div className={styles.search}>
          <span className={styles.searchIcon} aria-hidden>
            ⌕
          </span>
          <input
            type="search"
            placeholder={t.shell.searchFeed}
            aria-label={t.shell.searchFeed}
            className={styles.searchInput}
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>

      <Link to="/feed/new" className={styles.addRow}>
        <span className={styles.addAvatar} aria-hidden>
          +
        </span>
        <span className={styles.addText}>
          <strong>{t.shell.addEntry}</strong>
          <small>{t.shell.addEntryHint}</small>
        </span>
      </Link>

      <div className={styles.scroll} ref={scrollRef}>
        {query.isLoading ? (
          <p className={styles.empty}>{t.feed.loading}</p>
        ) : query.isError ? (
          <p className={styles.empty}>{t.feed.offline}</p>
        ) : stories.length === 0 ? (
          <p className={styles.empty}>{t.feed.empty}</p>
        ) : useVirtual ? (
          <div
            className={styles.virtualInner}
            style={{ height: virtualizer.getTotalSize() }}
          >
            {virtualizer.getVirtualItems().map((vItem) => {
              const story = stories[vItem.index]!;
              return (
                <ListRow
                  key={story.id}
                  to={`/feed/${story.id}`}
                  title={story.pseudonym}
                  subtitle={story.body}
                  time={timeAgo(story.published_at)}
                  avatarText={story.pseudonym}
                  active={activeId === story.id}
                  onMouseEnter={() => prefetchStory(story.id)}
                  onFocus={() => prefetchStory(story.id)}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: vItem.size,
                    transform: `translateY(${vItem.start}px)`,
                  }}
                />
              );
            })}
          </div>
        ) : (
          stories.map((story) => (
            <ListRow
              key={story.id}
              to={`/feed/${story.id}`}
              title={story.pseudonym}
              subtitle={story.body}
              time={timeAgo(story.published_at)}
              avatarText={story.pseudonym}
              active={activeId === story.id}
              onMouseEnter={() => prefetchStory(story.id)}
              onFocus={() => prefetchStory(story.id)}
            />
          ))
        )}

        {query.hasNextPage ? (
          <button
            type="button"
            className={styles.loadMore}
            disabled={query.isFetchingNextPage}
            onClick={() => void query.fetchNextPage()}
          >
            {query.isFetchingNextPage
              ? t.feed.loadMoreLoading
              : t.feed.loadMore}
          </button>
        ) : null}
      </div>
    </div>
  );
}
