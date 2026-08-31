import { describe, expect, it } from "vitest";

import {
  b58encode,
  challengeMessage,
  isValidSolanaAddress,
  signTipWalletChallenge,
} from "./wallet";

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

describe("challengeMessage", () => {
  it("matches the backend canonical template byte-for-byte", () => {
    expect(challengeMessage(" ABC ", "nonce1")).toBe(
      "de-press: verify wallet ownership\n" +
        "This signature proves you control this Solana address.\n" +
        "It grants no access to funds and expires in 10 minutes.\n" +
        "Address: ABC\n" +
        "Nonce: nonce1",
    );
  });
});

describe("b58encode", () => {
  it("encodes known vectors", () => {
    expect(b58encode(new TextEncoder().encode("hello world"))).toBe(
      "StV1DL6CwTryKyV",
    );
    expect(b58encode(new Uint8Array([0]))).toBe("1");
    expect(b58encode(new Uint8Array([0, 0, 1, 0]))).toBe("115R");
    expect(b58encode(new Uint8Array())).toBe("");
  });
});

describe("signTipWalletChallenge", () => {
  it("signs the exact canonical message via the injected wallet", async () => {
    let received: string | null = null;
    const sigBytes = new Uint8Array(64).fill(7);
    (globalThis as unknown as { window?: unknown }).window = {
      solana: {
        signMessage: async (msg: Uint8Array) => {
          received = new TextDecoder().decode(msg);
          return { signature: sigBytes };
        },
      },
    };
    try {
      const proof = await signTipWalletChallenge(WALLET);
      expect(received).toBe(challengeMessage(WALLET, proof.nonce));
      expect(proof.nonce).toMatch(/^[0-9a-f]{16}$/);
      expect(proof.signature).toBe(b58encode(sigBytes));
    } finally {
      delete (globalThis as unknown as { window?: unknown }).window;
    }
  });

  it("prefers the phantom namespace", async () => {
    const sigBytes = new Uint8Array(64);
    (globalThis as unknown as { window?: unknown }).window = {
      phantom: { solana: { signMessage: async () => ({ signature: sigBytes }) } },
      solana: { signMessage: async () => ({ signature: sigBytes }) },
    };
    try {
      const proof = await signTipWalletChallenge(WALLET);
      expect(proof.signature).toBe(b58encode(sigBytes));
    } finally {
      delete (globalThis as unknown as { window?: unknown }).window;
    }
  });

  it("throws when no wallet is injected", async () => {
    await expect(signTipWalletChallenge(WALLET)).rejects.toThrow(
      "No injected Solana wallet",
    );
  });
});