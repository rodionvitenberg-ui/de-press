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

  const [phase, setPhase] = useState<Phase>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [preview, setPreview] = useState<CircleRecording | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    if (preview?.objectUrl) URL.revokeObjectURL(preview.objectUrl);
    setPreview(null);
    setPhase("idle");
    setElapsed(0);
    setError(null);
  }, [clearTimers, preview, stopTracks]);

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

  async function startCamera() {
    setError(null);
    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setPhase("error");
      setError(labels.unsupported);
      return;
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
      setPhase("idle");
    } catch {
      setPhase("error");
      setError(labels.unsupported);
    }
  }

  useEffect(() => {
    if (open) void startCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      const objectUrl = URL.createObjectURL(blob);
      setPreview({ blob, durationMs, objectUrl });
      setPhase("preview");
      setElapsed(0);
      if (videoRef.current) {
        videoRef.current.srcObject = null;
        videoRef.current.src = objectUrl;
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

  function onRetake() {
    if (preview?.objectUrl) URL.revokeObjectURL(preview.objectUrl);
    setPreview(null);
    setPhase("idle");
    void startCamera();
  }

  if (!open) return null;

  const sec = Math.floor(elapsed / 1000);
  const maxSec = Math.floor(CIRCLE_MAX_MS / 1000);

  return (
    <div className={styles.backdrop} role="dialog" aria-modal="true" aria-label={labels.title}>
      <div className={styles.panel}>
        <header className={styles.head}>
          <h2 className={styles.title}>{labels.title}</h2>
          <button
            type="button"
            className={styles.close}
            onClick={() => {
              cleanup();
              onClose();
            }}
            aria-label={labels.cancel}
          >
            ×
          </button>
        </header>

        <p className={styles.hint}>{labels.ephemeralHint}</p>

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
              {labels.recording} {sec}s / {maxSec}s
            </span>
          ) : null}
        </div>

        {error || phase === "error" ? (
          <p className={styles.error}>{error || labels.unsupported}</p>
        ) : null}

        <div className={styles.actions}>
          {phase === "idle" || phase === "error" ? (
            <>
              <button
                type="button"
                className={styles.primary}
                onClick={() => startRecording()}
                disabled={phase === "error" || !streamRef.current}
              >
                {labels.start}
              </button>
              <button type="button" className={styles.ghost} onClick={onClose}>
                {labels.cancel}
              </button>
            </>
          ) : null}

          {phase === "live" ? (
            <button type="button" className={styles.stop} onClick={stopRecording}>
              {labels.stop}
            </button>
          ) : null}

          {phase === "preview" && preview ? (
            <>
              <p className={styles.previewMeta}>
                {labels.preview} · {Math.max(1, Math.round(preview.durationMs / 1000))}
                s
              </p>
              <button
                type="button"
                className={styles.primary}
                disabled={busy}
                onClick={() => void onSend()}
              >
                {labels.send}
              </button>
              <button
                type="button"
                className={styles.ghost}
                disabled={busy}
                onClick={onRetake}
              >
                {labels.retake}
              </button>
              <button
                type="button"
                className={styles.ghost}
                disabled={busy}
                onClick={() => {
                  cleanup();
                  onClose();
                }}
              >
                {labels.cancel}
              </button>
            </>
          ) : null}
        </div>

        <p className={styles.maxNote}>{labels.maxSec}</p>
      </div>
    </div>
  );
}
