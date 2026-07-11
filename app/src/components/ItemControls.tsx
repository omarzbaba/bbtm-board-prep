import { useEffect, useRef, useState } from "react";
import type { SourceReference } from "../types";
import { useLearner } from "../store/learnerStore";

/** Weak-item star toggle, keyed by item id. */
export function WeakStar({ itemId }: { itemId: string }) {
  const { state, toggleWeak } = useLearner();
  const on = !!state.weak_marks[itemId];
  return (
    <button className={`starbtn ${on ? "on" : ""}`} onClick={() => toggleWeak(itemId)}
      title={on ? "Unmark weak item" : "Mark as weak (needs review)"}
      aria-pressed={on} aria-label="Mark weak item">
      {on ? "★" : "☆"}
    </button>
  );
}

/** Inline learner note editor with autosave, keyed by item id. */
export function NoteEditor({ itemId }: { itemId: string }) {
  const { state, setNote } = useLearner();
  const saved = state.notes[itemId] || "";
  const [open, setOpen] = useState(!!saved);
  const [text, setText] = useState(saved);
  const timer = useRef<number | null>(null);

  useEffect(() => { setText(saved); if (saved) setOpen(true); }, [itemId, saved]);

  const onChange = (v: string) => {
    setText(v);
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setNote(itemId, v), 500);
  };

  if (!open) {
    return (
      <button className="btn ghost sm" onClick={() => setOpen(true)}>✎ Add note</button>
    );
  }
  return (
    <div className="stack gap-2" style={{ width: "100%" }}>
      <div className="row gap-2">
        <span className="eyebrow">My note</span>
        {text !== saved && <span className="muted" style={{ fontSize: 11 }}>saving…</span>}
        {text === saved && saved && <span className="muted" style={{ fontSize: 11, color: "var(--ok)" }}>saved ✓</span>}
      </div>
      <textarea className="textarea" value={text} placeholder="Your notes, mnemonics, or corrections…"
        onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

/** Source-trace display: shows the approved-source pointers backing an item. */
export function SourceTrace({ refs, confidence }: { refs: SourceReference[]; confidence?: string }) {
  const [open, setOpen] = useState(false);
  if (!refs || refs.length === 0) return null;
  return (
    <div className="panel trace stack gap-2">
      <button className="row gap-2" onClick={() => setOpen((o) => !o)}
        style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text)", padding: 0, width: "100%" }}>
        <span className="eyebrow" style={{ color: "var(--teal)" }}>▸ Source trace</span>
        <span className="muted" style={{ fontSize: 11 }}>{refs.length} reference{refs.length > 1 ? "s" : ""}</span>
        {confidence && <span className="tag" style={{ marginLeft: "auto" }}>support: {confidence}</span>}
      </button>
      {open && (
        <div className="stack">
          {refs.map((r, i) => (
            <div key={i} className="src-ref">
              <div className="row gap-2 wrap">
                <span className="mono" style={{ color: "var(--teal)" }}>{r.source_id}</span>
                {r.locator && <span className="muted" style={{ fontSize: 12 }}>· {r.locator}</span>}
                {r.confidence && <span className="tag">{r.confidence}</span>}
              </div>
              <div className="dim" style={{ fontSize: "var(--text-sm)", marginTop: 2 }}>{r.supports}</div>
            </div>
          ))}
          <p className="muted" style={{ fontSize: 11, marginTop: 4, marginBottom: 0 }}>
            Generated from approved NotebookLM study sources & the ABPath blueprint. Educational board-prep only — not institutional policy.
          </p>
        </div>
      )}
    </div>
  );
}
