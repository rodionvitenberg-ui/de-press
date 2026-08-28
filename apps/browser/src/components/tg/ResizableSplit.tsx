import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
import { useViewportMode } from "@/core/hooks/useViewportMode";
import {
  clampListWidth,
  readListWidth,
  tabletListWidth,
  writeListWidth,
} from "@/core/listWidth";
import { isSplitIndexPath } from "@/core/viewport";
import styles from "./ResizableSplit.module.css";

interface ResizableSplitProps {
  list: ReactNode;
  main: ReactNode;
}

/**
 * TG Desktop-style split: resizable list column + main pane.
 * Width persisted in localStorage; shared across feed/chat.
 */
export function ResizableSplit({ list, main }: ResizableSplitProps) {
  const mode = useViewportMode();
  const path = useLocation().pathname;
  const stacked = mode === "phone";
  const showList = !stacked || isSplitIndexPath(path);
  const showMain = !stacked || !isSplitIndexPath(path);
  const [width, setWidth] = useState(() => readListWidth());
  const widthRef = useRef(width);
  widthRef.current = width;
  const dragRef = useRef<{ startX: number; startW: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [viewportW, setViewportW] = useState(() =>
    typeof window === "undefined" ? 1280 : window.innerWidth,
  );

  useEffect(() => {
    const onResize = () => setViewportW(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const listPx =
    mode === "tablet" ? tabletListWidth(width, viewportW) : width;

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      e.preventDefault();
      dragRef.current = { startX: e.clientX, startW: widthRef.current };
      setDragging(true);
      e.currentTarget.setPointerCapture(e.pointerId);
    },
    [],
  );

  const onPointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.startX;
    const next = clampListWidth(dragRef.current.startW + dx);
    widthRef.current = next;
    setWidth(next);
  }, []);

  const endDrag = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current) return;
    dragRef.current = null;
    setDragging(false);
    writeListWidth(widthRef.current);
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  }, []);

  // Sync if another layout mounts after resize elsewhere
  useEffect(() => {
    const onStorage = (ev: StorageEvent) => {
      if (ev.key === "depress:list-width-v1" && ev.newValue) {
        const n = Number(ev.newValue);
        if (Number.isFinite(n)) setWidth(clampListWidth(n));
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const splitClass = [
    styles.split,
    dragging ? styles.dragging : "",
    stacked ? styles.splitStacked : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={splitClass}>
      <div
        className={showList ? styles.listCol : `${styles.listCol} ${styles.listHidden}`}
        style={
          stacked
            ? undefined
            : { width: `${listPx}px`, minWidth: `${listPx}px` }
        }
      >
        {list}
      </div>
      <div
        className={stacked ? `${styles.handle} ${styles.handleHidden}` : styles.handle}
        role="separator"
        aria-orientation="vertical"
        aria-valuenow={listPx}
        aria-valuemin={280}
        aria-valuemax={560}
        aria-hidden={stacked}
        aria-label="Resize list"
        tabIndex={stacked ? -1 : 0}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") {
            const next = clampListWidth(width - 16);
            setWidth(next);
            writeListWidth(next);
          } else if (e.key === "ArrowRight") {
            const next = clampListWidth(width + 16);
            setWidth(next);
            writeListWidth(next);
          }
        }}
      />
      <div className={showMain ? styles.main : `${styles.main} ${styles.mainHidden}`}>
        {main}
      </div>
    </div>
  );
}
