import { useCallback, useEffect, useState } from "react";
import { ENTER_ANTI_PANIC_EVENT } from "@/core/host/startParam";
import { setTelegramVerticalSwipes } from "@/core/host/telegram";
import { killAllSockets } from "@/core/ws/registry";

const STORAGE_KEY = "depress_anti_panic";

/**
 * Anti-Panic Protocol: global emergency UI mode.
 * On enter: kill all WebSockets, mark body, strip clutter.
 * On Mini App host: also discourage vertical swipe-to-close.
 * Deep-link `startapp=panic` dispatches ENTER_ANTI_PANIC_EVENT.
 */
export function useAntiPanic() {
  const [active, setActive] = useState(() => {
    try {
      return window.localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.body.classList.toggle("antiPanicActive", active);
    setTelegramVerticalSwipes(!active);
  }, [active]);

  const enter = useCallback(() => {
    killAllSockets();
    setActive(true);
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
  }, []);

  const exit = useCallback(() => {
    setActive(false);
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    const onDeepLink = () => enter();
    window.addEventListener(ENTER_ANTI_PANIC_EVENT, onDeepLink);
    return () => window.removeEventListener(ENTER_ANTI_PANIC_EVENT, onDeepLink);
  }, [enter]);

  return { active, enter, exit };
}
