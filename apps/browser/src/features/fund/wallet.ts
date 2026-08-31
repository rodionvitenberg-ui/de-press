/** Solana address helpers (ADR-0020). Base58: 32–44 chars, no 0/O/I/l. */
const BASE58_RE = /^[1-9A-HJ-NP-Za-km-z]+$/;
const B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

/** USDC (SPL) mint on Solana mainnet — used for wallet deep links. */
export const USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

export function isValidSolanaAddress(address: string): boolean {
  const value = address.trim();
  return value.length >= 32 && value.length <= 44 && BASE58_RE.test(value);
}

/** base58 (bitcoin/Solana alphabet) encoder for pubkey and signature bytes. */
export function b58encode(bytes: Uint8Array): string {
  let num = 0n;
  for (const byte of bytes) num = (num << 8n) | BigInt(byte);
  let out = "";
  while (num > 0n) {
    out = B58_ALPHABET[Number(num % 58n)] + out;
    num /= 58n;
  }
  let pad = 0;
  while (pad < bytes.length && bytes[pad] === 0) pad += 1;
  return "1".repeat(pad) + out;
}

/**
 * Canonical challenge signed by the injected wallet. MUST stay byte-for-byte
 * identical to _CHALLENGE in backend/apps/fund/services.py: the backend
 * rebuilds the signed message from (address, nonce) with no stored state.
 */
export function challengeMessage(address: string, nonce: string): string {
  return [
    "de-press: verify wallet ownership",
    "This signature proves you control this Solana address.",
    "It grants no access to funds and expires in 10 minutes.",
    `Address: ${address.trim()}`,
    `Nonce: ${nonce}`,
  ].join("\n");
}

export interface OwnershipProof {
  nonce: string;
  /** base58-encoded 64-byte ed25519 signature of challengeMessage(address, nonce). */
  signature: string;
}

function randomNonce(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(8));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

type InjectedSolana = {
  signMessage: (
    message: Uint8Array,
    encoding?: string,
  ) => Promise<{ signature: Uint8Array }>;
};

function injectedSolana(): InjectedSolana | null {
  const g = globalThis as unknown as {
    window?: { phantom?: { solana?: InjectedSolana }; solana?: InjectedSolana };
  };
  return g.window?.phantom?.solana ?? g.window?.solana ?? null;
}

/** An injected Solana wallet able to sign messages (Phantom, Solflare…). */
export function isWalletAvailable(): boolean {
  return typeof injectedSolana()?.signMessage === "function";
}

/**
 * Ask the injected wallet to sign the canonical ownership challenge
 * (ADR-0020 phase 2, off-chain — a message approval, never a transaction).
 * Throws when no wallet is injected or the user rejects the prompt.
 */
export async function signTipWalletChallenge(
  address: string,
): Promise<OwnershipProof> {
  const provider = injectedSolana();
  if (!provider || typeof provider.signMessage !== "function") {
    throw new Error("No injected Solana wallet");
  }
  const nonce = randomNonce();
  const message = challengeMessage(address, nonce);
  const res = await provider.signMessage(
    new TextEncoder().encode(message),
    "utf8",
  );
  return { nonce, signature: b58encode(res.signature) };
}