import { describe, expect, it } from "vitest";
import { isHashedAssetPath, isOpaqueNetworkPath } from "./pwa";

describe("isOpaqueNetworkPath", () => {
  it("never caches API, sockets, media, or docs", () => {
    expect(isOpaqueNetworkPath("/api/v1/stories")).toBe(true);
    expect(isOpaqueNetworkPath("/ws/feed/")).toBe(true);
    expect(isOpaqueNetworkPath("/media/x")).toBe(true);
    expect(isOpaqueNetworkPath("/docs")).toBe(true);
    expect(isOpaqueNetworkPath("/openapi.json")).toBe(true);
  });
  it("leaves the app shell alone", () => {
    expect(isOpaqueNetworkPath("/feed")).toBe(false);
    expect(isOpaqueNetworkPath("/assets/index-abc.js")).toBe(false);
  });
});

describe("isHashedAssetPath", () => {
  it("matches Vite hashed assets", () => {
    expect(isHashedAssetPath("/assets/index-abc.js")).toBe(true);
    expect(isHashedAssetPath("/feed")).toBe(false);
  });
});
