/**
 * Public surface of the shared API client (audit Q3): endpoints, ApiError
 * and all response types. Each frontend re-exports this from its
 * src/core/api/client.ts and src/core/api/types.ts shims.
 */
export { API_URL, ApiError, api } from "./client";
export type { AiStreamHandlers } from "./client";
export type * from "./types";
