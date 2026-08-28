"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import styles from "./VoiceRecorder.module.css";

interface VoiceRecorderProps {
  disabled?: boolean;
  onRecorded: (blob: Blob, durationMs: number) => void | Promise<void>;
  labels?: {
    record: string;
    stop: string;
    cancel: string;
    unsupported: string;
    recording: string;
  };
  className?: string;
}

const defaultLabels = {
  record: "Голос",
  stop: "Стоп",
  cancel: "Отмена",
  unsupported: "Запись недоступна в этом браузере",
  recording: "Запись…",
};

export function VoiceRecorder({
  disabled,
  onRecorded,
  labels = defaultLabels,
  className = "",
}: VoiceRecorderProps) {
  const [supported, setSupported] = useState(true);
  const [recording, setRecording] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [busy, setBusy] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAt = useRef(0);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    setSupported(
      typeof window !== "undefined" &&
        !!navigator.mediaDevices?.getUserMedia &&
        typeof MediaRecorder !== "undefined",
    );
    return () => {
      stopTracks();
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, []);

  function stopTracks() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }

  async function start() {
    if (!supported || disabled || busy) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "";
      const recorder = mime
        ? new MediaRecorder(stream, { mimeType: mime })
        : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const duration = Date.now() - startedAt.current;
        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        stopTracks();
        setRecording(false);
        if (tickRef.current) {
          clearInterval(tickRef.current);
          tickRef.current = null;
        }
        setElapsedMs(0);
        if (blob.size > 0) {
          setBusy(true);
          void Promise.resolve(onRecorded(blob, duration)).finally(() =>
            setBusy(false),
          );
        }
      };
      mediaRef.current = recorder;
      startedAt.current = Date.now();
      setElapsedMs(0);
      tickRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startedAt.current);
      }, 200);
      recorder.start(250);
      setRecording(true);
    } catch {
      setSupported(false);
      stopTracks();
    }
  }

  function stop() {
    const rec = mediaRef.current;
    if (rec && rec.state !== "inactive") {
      rec.stop();
    }
  }

  function cancel() {
    const rec = mediaRef.current;
    if (rec && rec.state !== "inactive") {
      rec.ondataavailable = null;
      rec.onstop = () => {
        stopTracks();
        setRecording(false);
        if (tickRef.current) clearInterval(tickRef.current);
        setElapsedMs(0);
      };
      rec.stop();
    } else {
      stopTracks();
      setRecording(false);
    }
  }

  if (!supported) {
    return <p className={styles.hint}>{labels.unsupported}</p>;
  }

  const secs = Math.floor(elapsedMs / 1000);

  return (
    <div className={`${styles.wrap} ${className}`.trim()}>
      {!recording ? (
        <Button
          variant="secondary"
          disabled={disabled || busy}
          onClick={() => void start()}
        >
          {busy ? "…" : labels.record}
        </Button>
      ) : (
        <>
          <span className={styles.rec} aria-live="polite">
            {labels.recording} {secs}s
          </span>
          <Button variant="primary" onClick={stop}>
            {labels.stop}
          </Button>
          <Button variant="ghost" onClick={cancel}>
            {labels.cancel}
          </Button>
        </>
      )}
    </div>
  );
}
