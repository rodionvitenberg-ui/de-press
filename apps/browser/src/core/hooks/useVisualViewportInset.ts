import { useEffect, useState } from "react";

/** Keyboard overlap: window height minus visible visualViewport. */
export function useVisualViewportInset(): number {
  const [inset, setInset] = useState(0);

  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const sync = () => {
      const next = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
      setInset(Math.round(next));
    };
    sync();
    vv.addEventListener("resize", sync);
    vv.addEventListener("scroll", sync);
    return () => {
      vv.removeEventListener("resize", sync);
      vv.removeEventListener("scroll", sync);
    };
  }, []);

  return inset;
}
