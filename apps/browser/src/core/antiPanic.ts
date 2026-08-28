export const ANTI_PANIC_KEY = "depress_anti_panic";

export function readAntiPanic(): boolean {
  try {
    return window.localStorage.getItem(ANTI_PANIC_KEY) === "1";
  } catch {
    return false;
  }
}

export function writeAntiPanic(on: boolean): void {
  try {
    if (on) window.localStorage.setItem(ANTI_PANIC_KEY, "1");
    else window.localStorage.removeItem(ANTI_PANIC_KEY);
  } catch {
    /* ignore quota / private mode */
  }
}
