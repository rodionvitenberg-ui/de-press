import { useCallback, useRef, useState } from "react";

export function useVoiceRecorder(
  onRecorded: (blob: Blob, durationMs: number) => void,
  unsupportedMessage: string,
): {
  recording: boolean;
  error: string | null;
  toggle: () => Promise<void>;
  clearError: () => void;
} {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAt = useRef(0);
  const cb = useRef(onRecorded);
  cb.current = onRecorded;

  const toggle = useCallback(async () => {
    if (recording) {
      mediaRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
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
        stream.getTracks().forEach((tr) => tr.stop());
        setRecording(false);
        if (blob.size > 0) cb.current(blob, duration);
      };
      mediaRef.current = recorder;
      startedAt.current = Date.now();
      recorder.start();
      setRecording(true);
      setError(null);
    } catch {
      setError(unsupportedMessage);
    }
  }, [recording, unsupportedMessage]);

  return {
    recording,
    error,
    toggle,
    clearError: () => setError(null),
  };
}
