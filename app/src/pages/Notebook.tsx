import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useContent } from "../store/contentStore";
import { useLearner } from "../store/learnerStore";
import { NoteEditor } from "../components/ItemControls";
import { DesignationBadge, Empty } from "../components/ui";
import { domainNumber, domainShort } from "../lib/util";
import type { Designation } from "../types";

interface Entry {
  id: string;
  kind: "question" | "case" | "orphan";
  title: string;
  context: string;
  domain: string;
  designation: Designation | null;
  note: string;
  weak: boolean;
  hasNote: boolean;
}

export function Notebook() {
  const { bundle } = useContent();
  const { state } = useLearner();
  const nav = useNavigate();
  const [query, setQuery] = useState("");
  const [showWeak, setShowWeak] = useState(false);

  const entries = useMemo<Entry[]>(() => {
    const qById = new Map(bundle!.questions.map((q) => [q.id, q]));
    const cById = new Map(bundle!.cases.map((c) => [c.id, c]));
    const ids = new Set<string>([
      ...Object.keys(state.notes).filter((id) => (state.notes[id] || "").trim()),
      ...(showWeak ? Object.keys(state.weak_marks).filter((id) => state.weak_marks[id]) : []),
    ]);
    const out: Entry[] = [];
    for (const id of ids) {
      const q = qById.get(id);
      const c = cById.get(id);
      const note = state.notes[id] || "";
      out.push({
        id,
        kind: q ? "question" : c ? "case" : "orphan",
        title: q ? q.subdomain || q.domain : c ? c.title : id,
        context: q ? q.stem : c ? c.clinical_setup : "(item not in current bank)",
        domain: q ? q.domain : c ? c.domains[0] || "" : "",
        designation: q ? q.designation : (c?.designation ?? null),
        note,
        weak: !!state.weak_marks[id],
        hasNote: !!note.trim(),
      });
    }
    const ql = query.trim().toLowerCase();
    return out
      .filter((e) => !ql || `${e.note} ${e.title} ${e.context} ${e.domain}`.toLowerCase().includes(ql))
      .sort((a, b) => (domainNumber(a.domain) - domainNumber(b.domain)) || a.id.localeCompare(b.id));
  }, [bundle, state, query, showWeak]);

  const noteCount = Object.values(state.notes).filter((n) => n.trim()).length;
  const weakCount = Object.values(state.weak_marks).filter(Boolean).length;

  const open = (e: Entry) => {
    if (e.kind === "case") nav(`/cases?open=${e.id}`);
    else nav(`/practice?focus=${e.id}`);
  };

  return (
    <div className="stack gap-4">
      <div className="stack gap-2">
        <h1 className="serif" style={{ fontSize: "var(--text-xl)" }}>My notebook</h1>
        <p className="dim" style={{ margin: 0 }}>
          Every note you write on a question or case is filed here, linked back to the item.
          {" "}<strong>{noteCount}</strong> note{noteCount !== 1 ? "s" : ""} · {weakCount} weak-marked.
        </p>
      </div>

      <div className="card pad row gap-3 wrap">
        <input className="input" style={{ maxWidth: 340 }} placeholder="Search my notes…"
          value={query} onChange={(e) => setQuery(e.target.value)} />
        <button className={`chip ${showWeak ? "on" : ""}`} onClick={() => setShowWeak((s) => !s)}>
          ★ Include weak-marked items
        </button>
        <span className="spacer" />
        <span className="muted" style={{ fontSize: "var(--text-sm)" }}>{entries.length} shown</span>
      </div>

      {entries.length === 0 ? (
        <Empty
          title={noteCount === 0 ? "No notes yet" : "Nothing matches"}
          body={noteCount === 0
            ? "While practicing a question or reading a case, tap “✎ Add note” to jot a mnemonic or correction — it will appear here, tied to that item."
            : "Try a different search, or turn off filters."}
        />
      ) : (
        <div className="stack gap-3">
          {entries.map((e) => (
            <div key={e.id} className="card pad stack gap-3">
              <div className="row gap-2 wrap">
                <span className={`badge ${e.kind === "case" ? "f" : "c"}`}>{e.kind === "case" ? "Case" : e.kind === "question" ? "Question" : "Item"}</span>
                <span className="mono muted">{e.id}</span>
                <DesignationBadge d={e.designation} />
                {e.domain && <span className="tag">{domainNumber(e.domain)}. {domainShort(e.domain)}</span>}
                {e.weak && <span style={{ color: "var(--gold)" }} title="weak-marked">★</span>}
                <span className="spacer" />
                <button className="btn ghost sm" onClick={() => open(e)}>Open item →</button>
              </div>
              <div>
                <strong style={{ fontSize: "var(--text-base)" }}>{e.title}</strong>
                <p className="dim" style={{ margin: "3px 0 0", fontSize: "var(--text-sm)", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                  {e.context}
                </p>
              </div>
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "var(--space-3)" }}>
                <NoteEditor itemId={e.id} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
