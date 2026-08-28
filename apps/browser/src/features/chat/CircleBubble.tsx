import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { useI18n } from "@/core/i18n/context";
import { SpeakerIcon } from "./VoiceBubble";
import styles from "./CircleBubble.module.css";

interface CircleBubbleProps {
  videoUrl: string;
  durationMs?: number | null;
  fromMe: boolean;
}

/** Progress-ring geometry (viewBox 100×100). */
const RING_R = 48.5;
const RING_C = 2 * Math.PI * RING_R;

/**
 * TG-like round video note: tap to play/pause with sound, thin progress
 * ring around the circle, small mute toggle while playing, no native
 * controls, no loop — on end it rewinds to the first frame.
 */
export function CircleBubble({ videoUrl, durationMs, fromMe }: CircleBubbleProps) {
  const { t } = useI18n();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const uid = useId();
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [progress, setProgress] = useState(0);

  // Only one circle (or voice note) plays at a time.
  useEffect(() => {
    const onOtherPlay = (e: Event) => {
      if ((e as CustomEvent<string>).detail !== uid) {
        const el = videoRef.current;
        if (el && !el.paused) el.pause();
        setPlaying(false);
      }
    };
    window.addEventListener("dp-circle-play", onOtherPlay);
    window.addEventListener("dp-voice-play", onOtherPlay);
    return () => {
      window.removeEventListener("dp-circle-play", onOtherPlay);
      window.removeEventListener("dp-voice-play", onOtherPlay);
    };
  }, [uid]);

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    const onTime = () => {
      const dur =
        Number.isFinite(el.duration) && el.duration > 0
          ? el.duration
          : durationMs && durationMs > 0
            ? durationMs / 1000
            : 0;
      setProgress(dur > 0 ? Math.min(1, el.currentTime / dur) : 0);
    };
    const onEnd = () => {
      setPlaying(false);
      setProgress(0);
      el.currentTime = 0;
    };
    el.addEventListener("timeupdate", onTime);
    el.addEventListener("ended", onEnd);
    return () => {
      el.removeEventListener("timeupdate", onTime);
      el.removeEventListener("ended", onEnd);
    };
  }, [durationMs]);

  async function toggle() {
    const el = videoRef.current;
    if (!el) return;
    if (el.paused || el.ended) {
      window.dispatchEvent(new CustomEvent("dp-circle-play", { detail: uid }));
      window.dispatchEvent(new CustomEvent("dp-voice-play", { detail: uid }));
      try {
        await el.play();
        setPlaying(true);
      } catch {
        /* stay paused if playback is unavailable */
      }
    } else {
      el.pause();
      setPlaying(false);
    }
  }

  function onKey(e: ReactKeyboardEvent<HTMLDivElement>) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      void toggle();
    }
  }

  return (
    <div className={fromMe ? styles.wrapMe : styles.wrapThem}>
      <div
        className={styles.stage}
        role="button"
        tabIndex={0}
        aria-label={playing ? t.chat.playerPause : t.chat.playerPlay}
        onClick={() => void toggle()}
        onKeyDown={onKey}
      >
        <div className={styles.ring}>
          <video
            ref={videoRef}
            className={styles.video}
            src={videoUrl}
            playsInline
            preload="metadata"
          />
          {!playing ? <span className={styles.playGlyph} aria-hidden /> : null}
        </div>
        <svg className={styles.ringSvg} viewBox="0 0 100 100" aria-hidden>
          <circle
            cx="50"
            cy="50"
            r={RING_R}
            fill="none"
            stroke="var(--accent-hope)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={RING_C}
            strokeDashoffset={RING_C * (1 - progress)}
            transform="rotate(-90 50 50)"
          />
        </svg>
        {playing ? (
          <button
            type="button"
            className={`${styles.muteBtn} ${muted ? styles.muteBtnOff : ""}`}
            onClick={(e) => {
              e.stopPropagation();
              const el = videoRef.current;
              const next = !muted;
              setMuted(next);
              if (el) el.muted = next;
            }}
            aria-label={muted ? t.chat.playerUnmute : t.chat.playerMute}
            aria-pressed={muted}
          >
            <SpeakerIcon muted={muted} />
          </button>
        ) : null}
      </div>
      <div className={styles.meta}>
        <span className={styles.badge}>{t.chat.circleEphemeral}</span>
        {durationMs != null && durationMs > 0 ? (
          <span className={styles.dur}>
            {Math.max(1, Math.round(durationMs / 1000))}s
          </span>
        ) : null}
      </div>
    </div>
  );
}

