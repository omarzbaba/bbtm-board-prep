import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from "react";
import type { ReactNode } from "react";
import type { AttemptState, LearnerState } from "../types";
import {
  cloudEnabled, emptyState, getLearnerId, loadCloud, loadLocal, mergeStates,
  saveCloud, saveLocal, setLearnerId as persistId,
} from "./persistence";

interface LearnerCtx {
  state: LearnerState;
  learnerId: string;
  syncStatus: "local" | "syncing" | "synced" | "offline";
  cloudEnabled: boolean;
  setNote: (itemId: string, note: string) => void;
  toggleWeak: (itemId: string) => void;
  recordAttempt: (qid: string, chosen: string, correct: boolean) => void;
  markCaseStage: (cid: string, stage: number, completed?: boolean) => void;
  changeLearnerId: (id: string) => void;
  resetAll: () => void;
}

const Ctx = createContext<LearnerCtx | null>(null);

const nowISO = () => new Date().toISOString();

export function LearnerProvider({ children }: { children: ReactNode }) {
  const [learnerId, setLid] = useState(getLearnerId());
  const [state, setState] = useState<LearnerState>(() => loadLocal());
  const [syncStatus, setSyncStatus] = useState<LearnerCtx["syncStatus"]>(cloudEnabled ? "syncing" : "local");
  const saveTimer = useRef<number | null>(null);

  // Initial cloud hydrate + merge
  useEffect(() => {
    let cancel = false;
    (async () => {
      if (!cloudEnabled) return;
      const cloud = await loadCloud(learnerId);
      if (cancel) return;
      if (cloud) {
        setState((local) => {
          const merged = mergeStates(local, cloud);
          saveLocal(merged);
          return merged;
        });
        setSyncStatus("synced");
      } else {
        setSyncStatus("synced");
      }
    })();
    return () => { cancel = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learnerId]);

  // Persist (debounced) on every change
  const persist = useCallback((next: LearnerState) => {
    saveLocal(next);
    if (!cloudEnabled) return;
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    setSyncStatus("syncing");
    saveTimer.current = window.setTimeout(async () => {
      const ok = await saveCloud(learnerId, next);
      setSyncStatus(ok ? "synced" : "offline");
    }, 900);
  }, [learnerId]);

  const update = useCallback((fn: (s: LearnerState) => LearnerState) => {
    setState((prev) => {
      const next = { ...fn(prev), updated_at: nowISO(), learner_id: learnerId };
      persist(next);
      return next;
    });
  }, [persist, learnerId]);

  const setNote = useCallback((itemId: string, note: string) => {
    update((s) => {
      const notes = { ...s.notes };
      if (note.trim()) notes[itemId] = note; else delete notes[itemId];
      return { ...s, notes };
    });
  }, [update]);

  const toggleWeak = useCallback((itemId: string) => {
    update((s) => {
      const weak_marks = { ...s.weak_marks };
      if (weak_marks[itemId]) delete weak_marks[itemId]; else weak_marks[itemId] = true;
      return { ...s, weak_marks };
    });
  }, [update]);

  const recordAttempt = useCallback((qid: string, chosen: string, correct: boolean) => {
    update((s) => {
      const prev: AttemptState = s.attempts[qid] || { seen: 0, correct: 0, box: 0 };
      const box = Math.max(0, Math.min(5, correct ? (prev.box || 0) + 1 : 0));
      return {
        ...s,
        attempts: {
          ...s.attempts,
          [qid]: {
            seen: (prev.seen || 0) + 1,
            correct: (prev.correct || 0) + (correct ? 1 : 0),
            last_choice: chosen,
            last_result: correct ? "correct" : "incorrect",
            last_seen_at: nowISO(),
            box,
          },
        },
      };
    });
  }, [update]);

  const markCaseStage = useCallback((cid: string, stage: number, completed = false) => {
    update((s) => {
      const cp = { ...(s.case_progress || {}) };
      const prev = cp[cid] || { completed: false, revealed_stages: [] as number[] };
      const revealed = prev.revealed_stages.includes(stage) ? prev.revealed_stages : [...prev.revealed_stages, stage];
      cp[cid] = { completed: completed || prev.completed, revealed_stages: revealed, last_seen_at: nowISO() };
      return { ...s, case_progress: cp };
    });
  }, [update]);

  const changeLearnerId = useCallback((id: string) => {
    persistId(id);
    const newId = getLearnerId();
    setLid(newId);
  }, []);

  const resetAll = useCallback(() => {
    const fresh = { ...emptyState(), learner_id: learnerId, updated_at: nowISO() };
    setState(fresh);
    persist(fresh);
  }, [learnerId, persist]);

  const value = useMemo<LearnerCtx>(() => ({
    state, learnerId, syncStatus, cloudEnabled,
    setNote, toggleWeak, recordAttempt, markCaseStage, changeLearnerId, resetAll,
  }), [state, learnerId, syncStatus, setNote, toggleWeak, recordAttempt, markCaseStage, changeLearnerId, resetAll]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useLearner(): LearnerCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useLearner must be used within LearnerProvider");
  return ctx;
}
