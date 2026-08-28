import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { Me } from "@/core/api/types";
import {
  bootstrapHost,
  type AppHostKind,
  type HostBootstrapResult,
} from "./bootstrap";
import { readStartParam } from "./startParam";
import { isTelegramHost } from "./telegram";

interface HostContextValue {
  host: AppHostKind;
  ready: boolean;
  isTelegram: boolean;
  me: Me | null;
  telegramAuthError: string | null;
  /** Raw Telegram / query start_param (may be empty). */
  startParam: string;
}

const HostContext = createContext<HostContextValue | null>(null);

export function HostProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [ready, setReady] = useState(false);
  const [result, setResult] = useState<HostBootstrapResult>({
    host: isTelegramHost() ? "telegram" : "browser",
    me: null,
    telegramAuthError: null,
  });

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const next = await bootstrapHost();
      if (cancelled) return;
      setResult(next);
      if (next.me) {
        queryClient.setQueryData(["me"], next.me);
      }
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [queryClient]);

  const value = useMemo<HostContextValue>(
    () => ({
      host: result.host,
      ready,
      isTelegram: result.host === "telegram",
      me: result.me,
      telegramAuthError: result.telegramAuthError,
      startParam: readStartParam(),
    }),
    [result, ready],
  );

  return (
    <HostContext.Provider value={value}>{children}</HostContext.Provider>
  );
}

export function useHost(): HostContextValue {
  const ctx = useContext(HostContext);
  if (!ctx) {
    throw new Error("useHost must be used within HostProvider");
  }
  return ctx;
}
