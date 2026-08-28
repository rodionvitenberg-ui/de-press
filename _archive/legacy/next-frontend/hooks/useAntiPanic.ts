"use client";

import { useCallback, useEffect, useState } from "react";
import { killAllSockets } from "@/lib/ws/registry";

const STORAGE_KEY = "depress_anti_panic";

/**
 * Anti-Panic Protocol: global emergency UI mode.
 * Interface: { active, enter, exit }.
 * On enter: kill all WebSockets, mark body, strip clutter.
 */
export function useAntiPanic() {
  const [active, setActive] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setActive(window.localStorage.getItem(STORAGE_KEY) === "1");
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    document.body.classList.toggle("antiPanicActive", active);
  }, [active]);

  const enter = useCallback(() => {
    killAllSockets();
    setActive(true);
    window.localStorage.setItem(STORAGE_KEY, "1");
  }, []);

  const exit = useCallback(() => {
    setActive(false);
    window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { active, enter, exit };
}
