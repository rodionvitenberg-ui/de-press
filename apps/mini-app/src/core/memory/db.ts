/**
 * Zero-Knowledge local memory — IndexedDB only.
 * Never sync raw mood maps to the server.
 */

const DB_NAME = "depress_zk";
const DB_VERSION = 2;
const STORE = "mood_entries";
const META = "meta";
const COMPANION_STORE = "companion_messages";

export interface MoodEntry {
  id: string;
  at: string;
  level: number;
  note: string;
  tags: string[];
}

export interface CompanionMessage {
  id: string;
  at: string;
  role: "user" | "assistant";
  content: string;
  crisis?: boolean;
}

export interface MemoryMeta {
  analyticsEnabled: boolean;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error ?? new Error("IndexedDB open failed"));
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: "id" });
        store.createIndex("at", "at", { unique: false });
      }
      if (!db.objectStoreNames.contains(META)) {
        db.createObjectStore(META, { keyPath: "key" });
      }
      if (!db.objectStoreNames.contains(COMPANION_STORE)) {
        const companion = db.createObjectStore(COMPANION_STORE, {
          keyPath: "id",
        });
        companion.createIndex("at", "at", { unique: false });
      }
    };
  });
}


function uuid(): string {
  return crypto.randomUUID();
}

export async function getMeta(): Promise<MemoryMeta> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(META, "readonly");
    const req = tx.objectStore(META).get("settings");
    req.onsuccess = () => {
      const row = req.result as { key: string; value: MemoryMeta } | undefined;
      resolve(row?.value ?? { analyticsEnabled: true });
    };
    req.onerror = () => reject(req.error);
  });
}

export async function setMeta(meta: MemoryMeta): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(META, "readwrite");
    tx.objectStore(META).put({ key: "settings", value: meta });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function addMoodEntry(input: {
  level: number;
  note?: string;
  tags?: string[];
}): Promise<MoodEntry> {
  const entry: MoodEntry = {
    id: uuid(),
    at: new Date().toISOString(),
    level: Math.min(5, Math.max(1, Math.round(input.level))),
    note: (input.note || "").slice(0, 500),
    tags: input.tags || [],
  };
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(entry);
    tx.oncomplete = () => resolve(entry);
    tx.onerror = () => reject(tx.error);
  });
}

export async function listMoodEntries(limit = 90): Promise<MoodEntry[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => {
      const rows = (req.result as MoodEntry[]).sort((a, b) =>
        a.at < b.at ? 1 : -1,
      );
      resolve(rows.slice(0, limit));
    };
    req.onerror = () => reject(req.error);
  });
}

export async function addCompanionMessage(
  role: "user" | "assistant",
  content: string,
  crisis?: boolean,
): Promise<CompanionMessage> {
  const message: CompanionMessage = {
    id: uuid(),
    at: new Date().toISOString(),
    role,
    content,
    ...(crisis ? { crisis: true } : {}),
  };
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(COMPANION_STORE, "readwrite");
    tx.objectStore(COMPANION_STORE).put(message);
    tx.oncomplete = () => resolve(message);
    tx.onerror = () => reject(tx.error);
  });
}

/** Chronological transcript (oldest first), capped to the last `limit`. */
export async function listCompanionMessages(
  limit = 200,
): Promise<CompanionMessage[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(COMPANION_STORE, "readonly");
    const req = tx.objectStore(COMPANION_STORE).getAll();
    req.onsuccess = () => {
      const rows = (req.result as CompanionMessage[]).sort((a, b) =>
        a.at < b.at ? -1 : 1,
      );
      resolve(rows.slice(-limit));
    };
    req.onerror = () => reject(req.error);
  });
}

export async function wipeAllMemory(): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE, META, COMPANION_STORE], "readwrite");
    tx.objectStore(STORE).clear();
    tx.objectStore(META).clear();
    tx.objectStore(COMPANION_STORE).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export function summarizePatterns(entries: MoodEntry[]): {
  count: number;
  avgLevel: number | null;
  last7: number;
  trend: "up" | "down" | "flat" | "unknown";
} {
  if (entries.length === 0) {
    return { count: 0, avgLevel: null, last7: 0, trend: "unknown" };
  }
  const avg =
    entries.reduce((s, e) => s + e.level, 0) / Math.max(entries.length, 1);
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
  const last7 = entries.filter((e) => new Date(e.at).getTime() >= weekAgo);
  const older = entries.filter((e) => new Date(e.at).getTime() < weekAgo);
  let trend: "up" | "down" | "flat" | "unknown" = "unknown";
  if (last7.length >= 2 && older.length >= 1) {
    const a = last7.reduce((s, e) => s + e.level, 0) / last7.length;
    const b = older.reduce((s, e) => s + e.level, 0) / older.length;
    if (a - b > 0.4) trend = "up";
    else if (b - a > 0.4) trend = "down";
    else trend = "flat";
  }
  return {
    count: entries.length,
    avgLevel: Math.round(avg * 10) / 10,
    last7: last7.length,
    trend,
  };
}
