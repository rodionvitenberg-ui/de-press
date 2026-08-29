import { useEffect, useRef, useState, type MouseEvent } from "react";
import { EmotionSticker, type GestureKey } from "./EmotionSticker";
import styles from "./FeedCloudPresence.module.css";

const FADE_MS = 1500;
const PLAY_MS = 4000;
const TOTAL_MS = FADE_MS + PLAY_MS + FADE_MS;
const WIGGLE_MS = 420;

type Phase = "in" | "play" | "out" | "wiggle";

function phaseFromElapsed(elapsed: number): Phase {
  if (elapsed < FADE_MS) return "in";
  if (elapsed < FADE_MS + PLAY_MS) return "play";
  return "out";
}

interface FeedCloudPresenceProps {
  gesture: GestureKey;
  label: string;
  startedAt: number;
  onGone: () => void;
}

export function FeedCloudPresence({
  gesture,
  label,
  startedAt,
  onGone,
}: FeedCloudPresenceProps) {
  const [phase, setPhase] = useState<Phase>(() =>
    phaseFromElapsed(Date.now() - startedAt),
  );
  const gone = useRef(false);
  const skipAuto = useRef(false);
  const onGoneRef = useRef(onGone);
  onGoneRef.current = onGone;

  useEffect(() => {
    gone.current = false;
    skipAuto.current = false;
    const timers: number[] = [];

    function later(ms: number, fn: () => void) {
      if (ms <= 0) {
        fn();
        return;
      }
      timers.push(window.setTimeout(fn, ms));
    }

    function finish() {
      if (gone.current) return;
      gone.current = true;
      onGoneRef.current();
    }

    const elapsed = Date.now() - startedAt;
    if (elapsed >= TOTAL_MS) {
      finish();
      return () => {};
    }

    const start = phaseFromElapsed(elapsed);
    setPhase(start);
    if (start === "in") {
      later(FADE_MS - elapsed, () => {
        if (!skipAuto.current) setPhase("play");
      });
      later(FADE_MS + PLAY_MS - elapsed, () => {
        if (!skipAuto.current) setPhase("out");
      });
      later(TOTAL_MS - elapsed, () => {
        if (!skipAuto.current) finish();
      });
    } else if (start === "play") {
      later(FADE_MS + PLAY_MS - elapsed, () => {
        if (!skipAuto.current) setPhase("out");
      });
      later(TOTAL_MS - elapsed, () => {
        if (!skipAuto.current) finish();
      });
    } else {
      later(TOTAL_MS - elapsed, () => {
        if (!skipAuto.current) finish();
      });
    }

    return () => {
      for (const id of timers) window.clearTimeout(id);
    };
  }, [startedAt]);

  const leaving = useRef(false);

  function finishNow() {
    if (gone.current) return;
    gone.current = true;
    onGoneRef.current();
  }

  function startOut() {
    if (leaving.current || gone.current) return;
    leaving.current = true;
    setPhase("out");
    window.setTimeout(finishNow, FADE_MS);
  }

  function onClick(ev: MouseEvent) {
    ev.preventDefault();
    ev.stopPropagation();
    if (skipAuto.current || leaving.current || gone.current) return;
    skipAuto.current = true;
    setPhase("wiggle");
    window.setTimeout(startOut, WIGGLE_MS);
  }

  return (
    <button
      type="button"
      className={`${styles.slot} ${styles[phase]}`}
      aria-label={label}
      title={label}
      onClick={onClick}
    >
      <span className={styles.motion}>
        <span
          className={styles.nudge}
          onAnimationEnd={(ev) => {
            if (ev.target !== ev.currentTarget) return;
            if (!skipAuto.current) return;
            startOut();
          }}
        >
          <EmotionSticker gesture={gesture} label={label} mini />
        </span>
      </span>
    </button>
  );
}

export { TOTAL_MS as FEED_CLOUD_TOTAL_MS };
