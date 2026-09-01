/**
 * Smoke tests for the API client wrapper (audit Q4): JSON parsing, error
 * surfacing with status, 204 handling, JSON Content-Type on bodies.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "./client";

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client request()", () => {
  it("parses JSON and sends same-origin credentials", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ username: "anon" }));
    vi.stubGlobal("fetch", fetchMock);

    const me = await api.me();

    expect(me).toEqual({ username: "anon" });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(url).toBe("/api/v1/me");
    expect(init.credentials).toBe("include");
  });

  it("surfaces backend detail as ApiError with status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ detail: "нет сессии" }, 401)),
    );

    await expect(api.me()).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "нет сессии",
    });
  });

  it("falls back to statusText when error body is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("nope", { status: 500 })),
    );

    const err = await api.me().catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(500);
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(null, { status: 204 })),
    );

    expect(await api.helperHeartbeat()).toBeUndefined();
  });

  it("sets JSON Content-Type when a body is sent", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await api.setHelperDuty(true);

    const [, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(new Headers(init.headers).get("Content-Type")).toBe(
      "application/json",
    );
  });
});
