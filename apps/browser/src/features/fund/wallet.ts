/** Solana address helpers (ADR-0020). Base58: 32–44 chars, no 0/O/I/l. */
const BASE58_RE = /^[1-9A-HJ-NP-Za-km-z]+$/;

/** USDC (SPL) mint on Solana mainnet — used for wallet deep links. */
export const USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

export function isValidSolanaAddress(address: string): boolean {
  const value = address.trim();
  return value.length >= 32 && value.length <= 44 && BASE58_RE.test(value);
}