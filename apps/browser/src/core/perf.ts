/** Client-only route timing. Never sent to the server. */

const STORAGE_KEY = "depress:tti-samples";
const MAX_SAMPLES = 40;

export interface RouteSample {
  route: string;
  ms: number;
  at: number;
}

export function recordRouteMs(route: string, ms: number): void {
  const sample: RouteSample = { route, ms: Math.round(ms), at: Date.now() };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    const prev: RouteSample[] = raw ? (JSON.parse(raw) as RouteSample[]) : [];
    const next = [...prev, sample].slice(-MAX_SAMPLES);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* ignore quota / private mode */
  }
  try {
    performance.mark(`route:${route}`);
  } catch {
    /* ignore */
  }
}

export function readRouteSamples(): RouteSample[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as RouteSample[]) : [];
  } catch {
    return [];
  }
}
