import { useRef, type PointerEvent } from "react";

const MOVE_PX = 10;
const HOLD_MS = 500;

export function useLongPress(
  onLongPress?: (pos: { clientX: number; clientY: number }) => void,
) {
  const timer = useRef<number | null>(null);
  const origin = useRef<{ x: number; y: number } | null>(null);
  const suppressClick = useRef(false);

  function clear() {
    if (timer.current != null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
    origin.current = null;
  }

  function onPointerDown(ev: PointerEvent) {
    if (!onLongPress) return;
    if (ev.pointerType === "mouse" && ev.button !== 0) return;
    const { clientX, clientY } = ev;
    origin.current = { x: clientX, y: clientY };
    timer.current = window.setTimeout(() => {
      timer.current = null;
      suppressClick.current = true;
      onLongPress({ clientX, clientY });
    }, HOLD_MS);
  }

  function onPointerMove(ev: PointerEvent) {
    if (!origin.current || timer.current == null) return;
    const dx = ev.clientX - origin.current.x;
    const dy = ev.clientY - origin.current.y;
    if (Math.hypot(dx, dy) > MOVE_PX) clear();
  }

  return {
    suppressClick,
    onPointerDown,
    onPointerMove,
    onPointerUp: clear,
    onPointerLeave: clear,
    onPointerCancel: clear,
  };
}
