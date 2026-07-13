// Persistence layer for per-learner state (progress, notes, weak-marks).
//
// LOCAL-FIRST: the app works fully offline with browser localStorage — no account,
// no backend required. This is the default and is enough for a single learner on
// her own device.
//
// OPTIONAL CLOUD SYNC: if VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY are provided
// at build time, state also syncs to a Supabase (PostgREST) table so progress is
// backed up and available across devices. Implemented with plain fetch — no extra
// dependency. See supabase/ for the schema and setup.
import type { LearnerState } from "../types";

const LS_KEY = "bbtm.learner.v1";
const LS_ID = "bbtm.learner.id";

export function emptyState(): LearnerState {
  return { version: 1, notes: {}, weak_marks: {}, attempts: {}, case_progress: {} };
}

export function getLearnerId(): string {
  let id = localStorage.getItem(LS_ID);
  if (!id) {
    id = "tala-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem(LS_ID, id);
  }
  return id;
}

export function setLearnerId(id: string) {
  const clean = id.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "").slice(0, 40);
  if (clean) localStorage.setItem(LS_ID, clean);
}

// ---- Local ----
export function loadLocal(): LearnerState {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return emptyState();
    const parsed = JSON.parse(raw) as LearnerState;
    return { ...emptyState(), ...parsed };
  } catch {
    return emptyState();
  }
}

export function saveLocal(state: LearnerState) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(state));
  } catch {
    /* quota — ignore */
  }
}

// ---- Optional Supabase (PostgREST) cloud sync ----
const SB_URL = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const SB_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
export const cloudEnabled = Boolean(SB_URL && SB_KEY);

function sbHeaders() {
  return {
    apikey: SB_KEY as string,
    Authorization: `Bearer ${SB_KEY}`,
    "Content-Type": "application/json",
  };
}

export async function loadCloud(learnerId: string): Promise<LearnerState | null> {
  if (!cloudEnabled) return null;
  try {
    const res = await fetch(
      `${SB_URL}/rest/v1/learner_states?learner_id=eq.${encodeURIComponent(learnerId)}&select=state`,
      { headers: sbHeaders() },
    );
    if (!res.ok) return null;
    const rows = (await res.json()) as Array<{ state: LearnerState }>;
    return rows[0]?.state ?? null;
  } catch {
    return null;
  }
}

export async function saveCloud(learnerId: string, state: LearnerState): Promise<boolean> {
  if (!cloudEnabled) return false;
  try {
    const res = await fetch(`${SB_URL}/rest/v1/learner_states`, {
      method: "POST",
      headers: { ...sbHeaders(), Prefer: "resolution=merge-duplicates,return=minimal" },
      body: JSON.stringify({ learner_id: learnerId, state, updated_at: new Date().toISOString() }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ---- Manual file backup / restore ----
// A portable third copy on top of localStorage + optional cloud sync — lets the
// learner keep a dated snapshot anywhere (external drive, email to self, etc.) and
// restore it later on any device, even with cloud sync off.
function isLearnerState(v: unknown): v is LearnerState {
  if (!v || typeof v !== "object") return false;
  const o = v as Record<string, unknown>;
  return o.version === 1 && typeof o.notes === "object" && typeof o.weak_marks === "object"
    && typeof o.attempts === "object";
}

export function downloadBackupFile(state: LearnerState, learnerId: string) {
  const payload = { ...state, learner_id: learnerId, exported_at: new Date().toISOString() };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const date = new Date().toISOString().slice(0, 10);
  a.href = url;
  a.download = `bbtm-progress-backup-${learnerId}-${date}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function readBackupFile(file: File): Promise<LearnerState> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read the file."));
    reader.onload = () => {
      try {
        const parsed: unknown = JSON.parse(String(reader.result));
        if (!isLearnerState(parsed)) {
          reject(new Error("This doesn't look like a BB/TM progress backup file."));
          return;
        }
        resolve(parsed);
      } catch {
        reject(new Error("This file isn't valid JSON."));
      }
    };
    reader.readAsText(file);
  });
}

// Merge two states preferring the most recent per-item (best-effort: cloud wins on
// counts, union of notes/marks). Simple last-write-wins on scalars.
export function mergeStates(a: LearnerState, b: LearnerState): LearnerState {
  const out = emptyState();
  out.learner_id = b.learner_id || a.learner_id;
  out.notes = { ...a.notes, ...b.notes };
  out.weak_marks = { ...a.weak_marks, ...b.weak_marks };
  out.attempts = { ...a.attempts };
  for (const [k, v] of Object.entries(b.attempts)) {
    const prev = out.attempts[k];
    out.attempts[k] = prev && (prev.seen || 0) > (v.seen || 0) ? prev : v;
  }
  out.case_progress = { ...(a.case_progress || {}), ...(b.case_progress || {}) };
  return out;
}
