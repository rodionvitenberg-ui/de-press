import { useCallback, useEffect, useRef, useState } from "react";
import styles from "./CircleRecorder.module.css";

/** Max circle length — short video note (TG-like). */
export const CIRCLE_MAX_MS = 60_000;

export interface CircleRecording {
  blob: Blob;
  durationMs: number;
  objectUrl: string;
}

interface CircleRecorderProps {
  open: boolean;
  onClose: () => void;
  onRecorded: (rec: CircleRecording) => void | Promise<void>;
  labels: {
    title: string;
    start: string;
    stop: string;
    send: string;
    retake: string;
    cancel: string;
    unsupported: string;
    recording: string;
    preview: string;
    ephemeralHint: string;
    maxSec: string;
    releaseHint: string;
  };
  busy?: boolean;
}

type Phase = "idle" | "live" | "preview" | "error";

/**
 * UI scaffold for Circle (video note): circular viewfinder, record, preview, send.
 * Does not depend on backend availability — parent handles upload.
 */
export function CircleRecorder({
  open,
  onClose,
  onRecorded,
  labels,
  busy = false,
}: CircleRecorderProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAt = useRef(0);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const maxTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Mirrors `phase` so the always-attached pointerup listener can branch
  // without re-binding mid-gesture.
  const phaseRef = useRef<Phase>("idle");
  // Latest recording; lets cleanup revoke the blob URL even when invoked
  // from a stale effect closure.
  const previewRef = useRef<CircleRecording | null>(null);

  const [phase, setPhase] = useState<Phase>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [preview, setPreview] = useState<CircleRecording | null>(null);
  const [error, setError] = useState<string | null>(null);

  phaseRef.current = phase;

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const clearTimers = useCallback(() => {
    if (tickRef.current) {
      clearInterval(tickRef.current);
      tickRef.current = null;
    }
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
  }, []);

  const cleanup = useCallback(() => {
    clearTimers();
    try {
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
    } catch {
      /* ignore */
    }
    recorderRef.current = null;
    stopTracks();
    if (previewRef.current?.objectUrl) {
      URL.revokeObjectURL(previewRef.current.objectUrl);
    }
    previewRef.current = null;
    setPreview(null);
    setPhase("idle");
    setElapsed(0);
    setError(null);
  }, [clearTimers, stopTracks]);

  useEffect(() => {
    if (!open) {
      cleanup();
      return;
    }
    return () => {
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only on open flip
  }, [open]);

  /** Opens camera+mic; resolves false (and shows the error) when unavailable. */
  async function startCamera(): Promise<boolean> {
    setError(null);
    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setError(labels.unsupported);
      return false;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 480 },
          height: { ideal: 480 },
        },
        audio: true,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        void videoRef.current.play();
      }
      return true;
    } catch {
      setError(labels.unsupported);
      return false;
    }
  }

  // Hold-to-record: opening starts the camera and recording right away;
  // releasing the pointer stops into preview (or cancels if too early).
  useEffect(() => {
    if (!open) {
      cleanup();
      return;
    }
    let cancelled = false;
    void (async () => {
      const ok = await startCamera();
      if (!cancelled && ok) startRecording();
    })();
    return () => {
      cancelled = true;
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- open flip only
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onUp = () => {
      if (phaseRef.current === "live") stopRecording();
      else if (phaseRef.current === "idle" || phaseRef.current === "error") {
        onClose();
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("pointerup", onUp);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("keydown", onKey);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- open flip only
  }, [open]);

  function stopRecording() {
    clearTimers();
    const rec = recorderRef.current;
    if (rec && rec.state === "recording") {
      rec.stop();
    }
  }

  function startRecording() {
    const stream = streamRef.current;
    if (!stream) return;

    chunksRef.current = [];
    const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
      ? "video/webm;codecs=vp9,opus"
      : MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus")
        ? "video/webm;codecs=vp8,opus"
        : MediaRecorder.isTypeSupported("video/webm")
          ? "video/webm"
          : "";

    const recorder = mime
      ? new MediaRecorder(stream, { mimeType: mime })
      : new MediaRecorder(stream);

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const durationMs = Date.now() - startedAt.current;
      const type = recorder.mimeType || "video/webm";
      const blob = new Blob(chunksRef.current, { type });
      const rec: CircleRecording = {
        blob,
        durationMs,
        objectUrl: URL.createObjectURL(blob),
      };
      previewRef.current = rec;
      setPreview(rec);
      setPhase("preview");
      setElapsed(0);
      if (videoRef.current) {
        videoRef.current.srcObject = null;
        videoRef.current.src = rec.objectUrl;
        void videoRef.current.play();
      }
    };

    recorderRef.current = recorder;
    startedAt.current = Date.now();
    setElapsed(0);
    setPhase("live");
    recorder.start(200);

    tickRef.current = setInterval(() => {
      setElapsed(Date.now() - startedAt.current);
    }, 200);

    maxTimerRef.current = setTimeout(() => {
      stopRecording();
    }, CIRCLE_MAX_MS);
  }

  async function onSend() {
    if (!preview || busy) return;
    await onRecorded(preview);
  }

  if (!open) return null;

  const sec = Math.floor(elapsed / 1000);
  const maxSec = Math.floor(CIRCLE_MAX_MS / 1000);
  const cancel = () => {
    cleanup();
    onClose();
  };

  return (
    <div
      className={styles.backdrop}
      role="dialog"
      aria-modal="false"
      aria-label={labels.title}
    >
      <div className={styles.panel}>
        <div className={styles.ring}>
          <video
            ref={videoRef}
            className={styles.video}
            playsInline
            muted={phase !== "preview"}
            autoPlay
            loop={phase === "preview"}
          />
          {phase === "live" ? (
            <span className={styles.recBadge} aria-live="polite">
              ● {labels.recording} {sec}s / {maxSec}s
            </span>
          ) : null}
        </div>

        {phase === "live" ? (
          <p className={styles.note}>{labels.releaseHint}</p>
        ) : null}

        {phase === "preview" && preview ? (
          <p className={styles.note}>
            {labels.preview} ·{" "}
            {Math.max(1, Math.round(preview.durationMs / 1000))}s ·{" "}
            {labels.ephemeralHint}
          </p>
        ) : null}

        {error || phase === "error" ? (
          <p className={styles.error}>{error || labels.unsupported}</p>
        ) : null}

        <div className={styles.actions}>
          {phase === "preview" ? (
            <>
              <button
                type="button"
                className={styles.primary}
                disabled={busy}
                onClick={() => void onSend()}
              >
                {labels.send}
              </button>
              <button type="button" className={styles.ghost} disabled={busy} onClick={cancel}>
                {labels.cancel}
              </button>
            </>
          ) : phase === "error" ? (
            <button type="button" className={styles.ghost} onClick={cancel}>
              {labels.cancel}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
