import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  clampListWidth,
  readListWidth,
  writeListWidth,
} from "@/core/listWidth";
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
  const [width, setWidth] = useState(() => readListWidth());
  const widthRef = useRef(width);
  widthRef.current = width;
  const dragRef = useRef<{ startX: number; startW: number } | null>(null);
  const [dragging, setDragging] = useState(false);

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

  return (
    <div className={dragging ? `${styles.split} ${styles.dragging}` : styles.split}>
      <div
        className={styles.listCol}
        style={{ width: `${width}px`, minWidth: `${width}px` }}
      >
        {list}
      </div>
      <div
        className={styles.handle}
        role="separator"
        aria-orientation="vertical"
        aria-valuenow={width}
        aria-valuemin={280}
        aria-valuemax={560}
        aria-label="Resize list"
        tabIndex={0}
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
      <div className={styles.main}>{main}</div>
    </div>
  );
}
