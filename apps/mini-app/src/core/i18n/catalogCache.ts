// Distinct DB name: the mini-app shares the origin (and IndexedDB) with the
// browser app, but their source catalogs differ — never clobber each other.
const DB_NAME = "depress_i18n_tg";
const STORE = "catalogs";
const VERSION = 1;

export interface CachedCatalog {
  lang: string;
  sourceHash: string;
  strings: Record<string, string>;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, VERSION);
    req.onerror = () => reject(req.error ?? new Error("i18n db"));
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "lang" });
      }
    };
  });
}

export async function getCachedCatalog(
  lang: string,
  sourceHash: string,
): Promise<Record<string, string> | null> {
  try {
    const db = await openDb();
    return await new Promise((resolve, reject) => {
      const req = db.transaction(STORE, "readonly").objectStore(STORE).get(lang);
      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        const row = req.result as CachedCatalog | undefined;
        if (!row || row.sourceHash !== sourceHash) {
          resolve(null);
          return;
        }
        resolve(row.strings);
      };
    });
  } catch {
    return null;
  }
}

export async function setCachedCatalog(
  lang: string,
  sourceHash: string,
  strings: Record<string, string>,
): Promise<void> {
  try {
    const db = await openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put({ lang, sourceHash, strings } satisfies CachedCatalog);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    /* private mode */
  }
}