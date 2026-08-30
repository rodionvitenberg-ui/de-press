import { describe, expect, it } from "vitest";
import { reduceCall, type CallState } from "./callMachine";

const IDLE: CallState = { name: "idle" };

describe("reduceCall — caller", () => {
  it("starts outgoing optimistically, then binds the server call id", () => {
    let s = reduceCall(IDLE, { t: "outgoing", callId: null });
    expect(s).toEqual({ name: "outgoing", callId: null });
    s = reduceCall(s, { t: "outgoing", callId: "c1" });
    expect(s).toEqual({ name: "outgoing", callId: "c1" });
  });

  it("outgoing → accepted → connected", () => {
    let s: CallState = { name: "outgoing", callId: "c1" };
    s = reduceCall(s, { t: "accepted" });
    expect(s).toEqual({ name: "connecting", callId: "c1", role: "caller" });
    s = reduceCall(s, { t: "connected" });
    if (s.name === "active") {
      expect(s.role).toBe("caller");
      expect(s.startedAt).toBeGreaterThan(0);
    } else {
      expect.fail("expected active");
    }
  });

  it("cancel ends with cancelled reason", () => {
    const s = reduceCall({ name: "outgoing", callId: "c1" }, { t: "ended", reason: "cancelled" });
    expect(s).toEqual({ name: "ended", reason: "cancelled" });
  });
});

describe("reduceCall — callee", () => {
  it("incoming → accepted → connected as callee", () => {
    let s = reduceCall(IDLE, { t: "incoming", callId: "c2" });
    expect(s).toEqual({ name: "incoming", callId: "c2" });
    s = reduceCall(s, { t: "accepted" });
    expect(s).toEqual({ name: "connecting", callId: "c2", role: "callee" });
    s = reduceCall(s, { t: "connected" });
    if (s.name === "active") expect(s.role).toBe("callee");
    else expect.fail("expected active");
  });
});

describe("reduceCall — guards", () => {
  it("ignores incoming while another call is in progress", () => {
    const s = reduceCall({ name: "outgoing", callId: "c1" }, { t: "incoming", callId: "c9" });
    expect(s).toEqual({ name: "outgoing", callId: "c1" });
  });

  it("ended swallows further events until dismissed", () => {
    let s: CallState = { name: "active", callId: "c1", role: "caller", startedAt: 1 };
    s = reduceCall(s, { t: "ended", reason: "hangup" });
    expect(s).toEqual({ name: "ended", reason: "hangup" });
    s = reduceCall(s, { t: "connected" });
    expect(s.name).toBe("ended");
    s = reduceCall(s, { t: "dismiss" });
    expect(s).toEqual({ name: "idle" });
  });

  it("ended on idle is a no-op", () => {
    expect(reduceCall(IDLE, { t: "ended", reason: "busy" })).toEqual({ name: "idle" });
  });
});
