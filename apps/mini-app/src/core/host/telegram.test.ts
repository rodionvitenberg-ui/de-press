/**
 * Smoke tests for Telegram host detection (audit Q4): node env has no
 * window (browser host), a stubbed Telegram.WebApp is detected by its
 * non-empty signed initData.
 */
import { afterEach, describe, expect, it } from "vitest";
import { getTelegramWebApp, isTelegramHost, type TelegramWebApp } from "./telegram";

const webAppStub = (initData: string): TelegramWebApp => ({
  initData,
  initDataUnsafe: {},
  version: "7.10",
  platform: "weba",
  colorScheme: "dark",
  themeParams: {},
  isExpanded: true,
  viewportStableHeight: 600,
  ready: () => {},
  expand: () => {},
  close: () => {},
  onEvent: () => {},
  offEvent: () => {},
  BackButton: {
    isVisible: false,
    show: () => {},
    hide: () => {},
    onClick: () => {},
    offClick: () => {},
  },
});

const setWindowTelegram = (wa: TelegramWebApp | null): void => {
  (globalThis as Record<string, unknown>).window = {
    Telegram: wa ? { WebApp: wa } : undefined,
  };
};

afterEach(() => {
  delete (globalThis as Record<string, unknown>).window;
});

describe("Telegram host detection", () => {
  it("reports browser host when window is absent (node)", () => {
    expect(getTelegramWebApp()).toBeNull();
    expect(isTelegramHost()).toBe(false);
  });

  it("detects Telegram host with non-empty initData", () => {
    setWindowTelegram(webAppStub("query_id=AA&signature=ok"));
    expect(getTelegramWebApp()?.platform).toBe("weba");
    expect(isTelegramHost()).toBe(true);
  });

  it("rejects Telegram shell with empty initData", () => {
    setWindowTelegram(webAppStub(""));
    expect(isTelegramHost()).toBe(false);
  });
});
