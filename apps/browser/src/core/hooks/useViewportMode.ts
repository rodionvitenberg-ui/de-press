import { useEffect, useState } from "react";
import {
  BP_PHONE_MAX,
  BP_TABLET_MAX,
  modeFromWidth,
  type ViewportMode,
} from "@/core/viewport";

function readMode(): ViewportMode {
  if (typeof window === "undefined") return "desktop";
  return modeFromWidth(window.innerWidth);
}

function applyLayout(mode: ViewportMode): void {
  document.documentElement.dataset.layout = mode;
}

export function useViewportMode(): ViewportMode {
  const [mode, setMode] = useState<ViewportMode>(readMode);

  useEffect(() => {
    applyLayout(mode);
  }, [mode]);

  useEffect(() => {
    const phone = window.matchMedia(`(max-width: ${BP_PHONE_MAX}px)`);
    const tablet = window.matchMedia(`(max-width: ${BP_TABLET_MAX}px)`);
    const sync = () => {
      const next = readMode();
      setMode(next);
      applyLayout(next);
    };
    sync();
    phone.addEventListener("change", sync);
    tablet.addEventListener("change", sync);
    return () => {
      phone.removeEventListener("change", sync);
      tablet.removeEventListener("change", sync);
    };
  }, []);

  return mode;
}
