/**
 * Pure state machine for the 1:1 call UI (ADR 0021). Deliberately free of
 * WebRTC/React so it is unit-testable without a browser.
 */

export type CallRole = "caller" | "callee";

export type CallEndReason =
  | "hangup"
  | "declined"
  | "busy"
  | "timeout"
  | "connection"
  | "closed"
  | "cancelled"
  | "error";

export type CallState =
  | { name: "idle" }
  | { name: "outgoing"; callId: string | null }
  | { name: "incoming"; callId: string }
  | { name: "connecting"; callId: string; role: CallRole }
  | { name: "active"; callId: string; role: CallRole; startedAt: number }
  | { name: "ended"; reason: CallEndReason };

export type CallIntent =
  | { t: "outgoing"; callId: string | null }
  | { t: "incoming"; callId: string }
  | { t: "accepted" }
  | { t: "connected" }
  | { t: "ended"; reason: CallEndReason }
  | { t: "dismiss" };

export function reduceCall(state: CallState, intent: CallIntent): CallState {
  switch (intent.t) {
    case "outgoing":
      if (state.name === "outgoing") {
        return { ...state, callId: intent.callId ?? state.callId };
      }
      if (state.name === "idle" || state.name === "ended") {
        return { name: "outgoing", callId: intent.callId };
      }
      return state;
    case "incoming":
      if (state.name === "idle" || state.name === "ended") {
        return { name: "incoming", callId: intent.callId };
      }
      return state;
    case "accepted":
      if (state.name === "outgoing") {
        return { name: "connecting", callId: state.callId ?? "", role: "caller" };
      }
      if (state.name === "incoming") {
        return { name: "connecting", callId: state.callId, role: "callee" };
      }
      return state;
    case "connected":
      if (state.name === "connecting") {
        return {
          name: "active",
          callId: state.callId,
          role: state.role,
          startedAt: Date.now(),
        };
      }
      return state;
    case "ended":
      if (state.name === "idle") return state;
      return { name: "ended", reason: intent.reason };
    case "dismiss":
      return state.name === "ended" ? { name: "idle" } : state;
  }
}
