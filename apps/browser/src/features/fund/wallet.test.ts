import { describe, expect, it } from "vitest";

import { isValidSolanaAddress } from "./wallet";

const WALLET = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM";

describe("isValidSolanaAddress", () => {
  it("accepts a standard mainnet pubkey", () => {
    expect(isValidSolanaAddress(WALLET)).toBe(true);
    expect(isValidSolanaAddress(`  ${WALLET}  `)).toBe(true);
  });

  it("rejects wrong length", () => {
    expect(isValidSolanaAddress("abc")).toBe(false);
    expect(isValidSolanaAddress(WALLET.slice(0, 31))).toBe(false);
    expect(isValidSolanaAddress(WALLET + "A")).toBe(false);
    expect(isValidSolanaAddress("")).toBe(false);
  });

  it("rejects non-base58 characters", () => {
    expect(isValidSolanaAddress("0" + WALLET.slice(1))).toBe(false);
    expect(isValidSolanaAddress(WALLET.slice(0, 43) + "O")).toBe(false);
    expect(isValidSolanaAddress("О" + WALLET.slice(1))).toBe(false); // Cyrillic О
    expect(isValidSolanaAddress(WALLET.slice(0, 21) + " " + WALLET.slice(22))).toBe(
      false,
    );
  });
});