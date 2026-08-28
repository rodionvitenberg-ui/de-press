"use client";

import { useCallback, useEffect, useState } from "react";
import {
  addMoodEntry,
  getMeta,
  listMoodEntries,
  setMeta,
  summarizePatterns,
  wipeAllMemory,
  type MemoryMeta,
  type MoodEntry,
} from "@/lib/memory/db";

/**
 * Zero-Knowledge local memory.
 * Interface: entries, meta, add, toggleAnalytics, wipe, summary.
 */
export function useLocalMemory() {
  const [entries, setEntries] = useState<MoodEntry[]>([]);
  const [meta, setMetaState] = useState<MemoryMeta>({ analyticsEnabled: true });
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [e, m] = await Promise.all([listMoodEntries(), getMeta()]);
      setEntries(e);
      setMetaState(m);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "IndexedDB недоступен");
    } finally {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const add = useCallback(
    async (level: number, note?: string) => {
      if (!meta.analyticsEnabled) {
        throw new Error("Локальная аналитика выключена");
      }
      await addMoodEntry({ level, note });
      await refresh();
    },
    [meta.analyticsEnabled, refresh],
  );

  const toggleAnalytics = useCallback(
    async (enabled: boolean) => {
      const next = { analyticsEnabled: enabled };
      await setMeta(next);
      setMetaState(next);
    },
    [],
  );

  const wipe = useCallback(async () => {
    await wipeAllMemory();
    setEntries([]);
    setMetaState({ analyticsEnabled: true });
  }, []);

  const summary = summarizePatterns(entries);

  return {
    ready,
    error,
    entries,
    meta,
    summary,
    add,
    toggleAnalytics,
    wipe,
    refresh,
  };
}
