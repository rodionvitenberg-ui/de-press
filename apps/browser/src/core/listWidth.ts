/** Resizable list column width — shared by Feed + Chat (TG Desktop feel). */

export const LIST_WIDTH_DEFAULT = 424;
export const LIST_WIDTH_MIN = 280;
export const LIST_WIDTH_MAX = 560;

const STORAGE_KEY = "depress:list-width-v1";

export function clampListWidth(px: number): number {
  return Math.min(LIST_WIDTH_MAX, Math.max(LIST_WIDTH_MIN, Math.round(px)));
}

/** Visual clamp for tablet split. Does not persist. */
export function tabletListWidth(storedPx: number, viewportWidth: number): number {
  return Math.min(storedPx, Math.round(viewportWidth * 0.4));
}

export function readListWidth(): number {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return LIST_WIDTH_DEFAULT;
    const n = Number(raw);
    if (Number.isFinite(n)) return clampListWidth(n);
  } catch {
    /* ignore */
  }
  return LIST_WIDTH_DEFAULT;
}

export function writeListWidth(px: number): void {
  try {
    localStorage.setItem(STORAGE_KEY, String(clampListWidth(px)));
  } catch {
    /* ignore */
  }
}
