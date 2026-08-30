import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/core/api/client";
import type { CallSignalEvent } from "@/core/hooks/useChatSocket";
import {
  reduceCall,
  type CallEndReason,
  type CallIntent,
  type CallState,
} from "./callMachine";

const ICE_CACHE_TTL_MS = 5 * 60_000;
const ENDED_DISMISS_MS = 2_600;

let iceCache: { at: number; servers: RTCIceServer[] } | null = null;

async function iceServers(): Promise<RTCIceServer[]> {
  if (iceCache && Date.now() - iceCache.at < ICE_CACHE_TTL_MS) {
    return iceCache.servers;
  }
  try {
    const cfg = await api.rtcConfig();
    iceCache = { at: Date.now(), servers: cfg.ice_servers ?? [] };
  } catch {
    iceCache = { at: Date.now(), servers: [] };
  }
  return iceCache.servers;
}

export type SendCallFn = (msg: Record<string, unknown>) => void;

export interface CallController {
  state: CallState;
  muted: boolean;
  onSignal: (ev: CallSignalEvent) => void;
  onSocketDown: () => void;
  start: () => void;
  accept: () => Promise<void>;
  decline: () => void;
  cancel: () => void;
  hangup: () => void;
  toggleMute: () => void;
}

/**
 * Live 1:1 voice controller (ADR 0021): wires the pure call machine to the
 * dialogue WS signaling relay and a P2P audio-only RTCPeerConnection.
 */
export function useCall(send: SendCallFn): CallController {
  const [state, setState] = useState<CallState>({ name: "idle" });
  const [muted, setMuted] = useState(false);

  const sendRef = useRef(send);
  sendRef.current = send;
  const stateRef = useRef<CallState>(state);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const pendingOfferRef = useRef<string | null>(null);

  const dispatch = useCallback((intent: CallIntent) => {
    const next = reduceCall(stateRef.current, intent);
    if (next !== stateRef.current) {
      stateRef.current = next;
      setState(next);
    }
  }, []);

  const teardown = useCallback(() => {
    const pc = pcRef.current;
    pcRef.current = null;
    if (pc) {
      pc.onicecandidate = null;
      pc.onconnectionstatechange = null;
      pc.ontrack = null;
      try {
        pc.close();
      } catch {
        /* ignore */
      }
    }
    localStreamRef.current?.getTracks().forEach((t) => t.stop());
    localStreamRef.current = null;
    const audio = audioRef.current;
    if (audio) {
      audio.srcObject = null;
      audio.pause();
    }
    audioRef.current = null;
    pendingOfferRef.current = null;
    setMuted(false);
  }, []);

  const endLocal = useCallback(
    (reason: CallEndReason, notifyServer: boolean) => {
      const wasLive = stateRef.current.name !== "idle";
      teardown();
      if (notifyServer && wasLive) sendRef.current({ type: "call.end" });
      dispatch({ t: "ended", reason });
    },
    [dispatch, teardown],
  );

  const ensureAudio = useCallback((): HTMLAudioElement => {
    if (!audioRef.current) {
      const el = new Audio();
      el.autoplay = true;
      audioRef.current = el;
    }
    return audioRef.current;
  }, []);

  const makePC = useCallback(async (): Promise<RTCPeerConnection> => {
    const servers = await iceServers();
    const pc = new RTCPeerConnection({ iceServers: servers });
    pc.onicecandidate = (e) => {
      if (e.candidate) {
        sendRef.current({ type: "call.ice", candidate: e.candidate.toJSON() });
      }
    };
    pc.ontrack = (e) => {
      const audio = ensureAudio();
      audio.srcObject = e.streams[0];
      void audio.play().catch(() => {
        /* autoplay guard: user gesture usually present */
      });
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "connected") {
        dispatch({ t: "connected" });
      } else if (pc.connectionState === "failed") {
        endLocal("error", true);
      }
    };
    pcRef.current = pc;
    return pc;
  }, [dispatch, endLocal, ensureAudio]);

  const applyOffer = useCallback(async (sdp: string) => {
    const pc = pcRef.current;
    if (!pc) return;
    await pc.setRemoteDescription({ type: "offer", sdp });
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    sendRef.current({ type: "call.answer", sdp: answer.sdp });
  }, []);

  const onSignal = useCallback(
    (ev: CallSignalEvent) => {
      switch (ev.type) {
        case "call.outgoing":
          if (ev.call_id) dispatch({ t: "outgoing", callId: ev.call_id });
          break;
        case "call.incoming":
          if (typeof ev.call_id === "string") {
            dispatch({ t: "incoming", callId: ev.call_id });
          }
          break;
        case "call.accepted":
          dispatch({ t: "accepted" });
          break;
        case "call.offer":
          if (typeof ev.sdp !== "string") break;
          if (pcRef.current) void applyOffer(ev.sdp);
          else pendingOfferRef.current = ev.sdp;
          break;
        case "call.answer":
          if (typeof ev.sdp === "string" && pcRef.current) {
            void pcRef.current
              .setRemoteDescription({ type: "answer", sdp: ev.sdp })
              .catch(() => endLocal("error", true));
          }
          break;
        case "call.ice":
          if (pcRef.current && ev.candidate) {
            void pcRef.current
              .addIceCandidate(ev.candidate as RTCIceCandidateInit)
              .catch(() => {
                /* late/stray candidates are harmless */
              });
          }
          break;
        case "call.ended":
          teardown();
          dispatch({
            t: "ended",
            reason: (ev.reason as CallEndReason) || "hangup",
          });
          break;
        case "call.busy":
          teardown();
          dispatch({ t: "ended", reason: "busy" });
          break;
      }
    },
    [applyOffer, dispatch, endLocal, teardown],
  );

  const start = useCallback(() => {
    if (stateRef.current.name !== "idle") return;
    dispatch({ t: "outgoing", callId: null });
    sendRef.current({ type: "call.ring" });
  }, [dispatch]);

  const accept = useCallback(async () => {
    if (stateRef.current.name !== "incoming") return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      localStreamRef.current = stream;
      const pc = await makePC();
      stream.getTracks().forEach((t) => pc.addTrack(t, stream));
      dispatch({ t: "accepted" });
      sendRef.current({ type: "call.accept" });
      const sdp = pendingOfferRef.current;
      pendingOfferRef.current = null;
      if (sdp) await applyOffer(sdp);
    } catch {
      // No mic permission / device busy — honest local failure.
      teardown();
      dispatch({ t: "ended", reason: "error" });
    }
  }, [applyOffer, dispatch, makePC, teardown]);

  const decline = useCallback(() => {
    sendRef.current({ type: "call.decline" });
    teardown();
    dispatch({ t: "ended", reason: "declined" });
  }, [dispatch, teardown]);

  const cancel = useCallback(() => {
    endLocal("cancelled", true);
  }, [endLocal]);

  const hangup = useCallback(() => {
    endLocal("hangup", true);
  }, [endLocal]);

  const toggleMute = useCallback(() => {
    const stream = localStreamRef.current;
    if (!stream) return;
    const next = !muted;
    stream.getAudioTracks().forEach((t) => {
      t.enabled = !next;
    });
    setMuted(next);
  }, [muted]);

  const onSocketDown = useCallback(() => {
    const name = stateRef.current.name;
    if (name === "idle" || name === "ended") return;
    endLocal("connection", false);
  }, [endLocal]);

  // Auto-dismiss the ended card.
  useEffect(() => {
    if (state.name !== "ended") return;
    const timer = setTimeout(() => dispatch({ t: "dismiss" }), ENDED_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [state, dispatch]);

  // Unmount / Anti-Panic socket kill: stop tracks, close the peer connection.
  useEffect(() => teardown, [teardown]);

  return {
    state,
    muted,
    onSignal,
    onSocketDown,
    start,
    accept,
    decline,
    cancel,
    hangup,
    toggleMute,
  };
}
