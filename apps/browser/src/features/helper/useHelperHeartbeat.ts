import { useEffect } from "react";
import { api } from "@/core/api/client";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";

const INTERVAL_MS = 20_000;

/** Helper with /chat or /helper open: ping so instant match can find them. */
export function useHelperHeartbeat(enabled: boolean): void {
  const { active: panic } = useAntiPanic();
  const on = enabled && !panic;

  useEffect(() => {
    if (!on) return;
    const ping = () => {
      void api.helperHeartbeat().catch(() => {
        /* offline / not a Helper — wait for next tick */
      });
    };
    ping();
    const id = window.setInterval(ping, INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [on]);
}
