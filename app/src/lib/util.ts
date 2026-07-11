import type { BoardQuestion, Designation } from "../types";

export const DESIGNATION_LABEL: Record<Designation, string> = {
  C: "Core",
  AR: "Advanced Resident",
  F: "Fellow",
};

export const DESIGNATION_CLASS: Record<Designation, string> = { C: "c", AR: "ar", F: "f" };

export const STATUS_LABEL: Record<string, string> = {
  covered: "Covered",
  "strong-partial": "Strong partial",
  "weak-partial": "Weak partial",
  thin: "Thin",
  uncertain: "Uncertain",
  missing: "Missing",
};

export function domainNumber(domain: string): number {
  const m = domain.match(/^(\d+)/);
  return m ? parseInt(m[1], 10) : 999;
}

export function domainShort(domain: string): string {
  // "6. Hazards of Transfusion: Specific Adverse Events" -> "Hazards of Transfusion"
  const body = domain.replace(/^\d+\.\s*/, "");
  return body.split(":")[0].trim();
}

export function pct(n: number): string {
  return `${Math.round(n * 100)}%`;
}

/** Deterministic per-question option order (stable across renders, varies by id).
 *  `h` is kept unsigned (>>> 0) throughout — Math.imul returns a *signed* 32-bit
 *  int, and a negative `h` would make `j = h % (i+1)` negative, producing an
 *  out-of-range index and undefined array holes. */
export function stableShuffle<T>(arr: T[], seed: string): T[] {
  const a = [...arr];
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  for (let i = a.length - 1; i > 0; i--) {
    h = (Math.imul(h, 48271) + 12345) >>> 0;
    const j = h % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function reviewNeedsAttention(q: BoardQuestion): boolean {
  return q.review?.status === "needs-human-review" || q.review?.source_support === "uncertain";
}

export function accuracy(seen: number, correct: number): number {
  return seen > 0 ? correct / seen : 0;
}
