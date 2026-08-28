import { useCallback, useEffect, useState } from "react";
import { isIosSafari, isStandalone } from "@/core/pwa";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function usePwaInstall(): {
  canInstall: boolean;
  isStandalone: boolean;
  isIos: boolean;
  prompt: () => Promise<void>;
} {
  const [standalone, setStandalone] = useState(isStandalone);
  const [ios] = useState(isIosSafari);
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(
    null,
  );

  useEffect(() => {
    setStandalone(isStandalone());
    const onPrompt = (event: Event) => {
      event.preventDefault();
      setDeferred(event as BeforeInstallPromptEvent);
    };
    const onInstalled = () => {
      setDeferred(null);
      setStandalone(true);
    };
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const prompt = useCallback(async () => {
    if (!deferred) return;
    await deferred.prompt();
    setDeferred(null);
  }, [deferred]);

  return {
    canInstall: Boolean(deferred) && !standalone,
    isStandalone: standalone,
    isIos: ios && !standalone,
    prompt,
  };
}
