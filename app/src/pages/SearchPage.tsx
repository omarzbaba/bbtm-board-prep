import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useContent } from "../store/contentStore";
import { search } from "../lib/search";
import { domainShort } from "../lib/util";

export function SearchPage() {
  const { bundle } = useContent();
  const [q, setQ] = useState("");
  const nav = useNavigate();
  const hits = useMemo(() => search(q, bundle!.questions, bundle!.cases), [q, bundle]);

  return (
    <div className="stack gap-4">
      <div className="stack gap-2">
        <h1 className="serif" style={{ fontSize: "var(--text-xl)" }}>Search the bank</h1>
        <p className="dim" style={{ margin: 0 }}>Find questions and cases by keyword, entity, or domain.</p>
      </div>
      <input className="input" autoFocus placeholder="e.g. TRALI, delayed hemolytic reaction, RhIG, TTP…"
        value={q} onChange={(e) => setQ(e.target.value)} style={{ fontSize: "var(--text-md)", padding: "12px 16px" }} />

      {q.length >= 2 && (
        <p className="muted" style={{ fontSize: "var(--text-sm)", margin: 0 }}>{hits.length} result{hits.length !== 1 ? "s" : ""}</p>
      )}
      <div className="stack gap-2">
        {hits.map((h) => (
          <button key={h.kind + h.id} className="card card-hover pad stack gap-2"
            style={{ textAlign: "left", cursor: "pointer", color: "inherit" }}
            onClick={() => nav(h.kind === "case" ? "/cases" : `/practice?domain=${encodeURIComponent(h.domain)}`)}>
            <div className="row gap-2 wrap">
              <span className={`badge ${h.kind === "case" ? "f" : "c"}`}>{h.kind === "case" ? "Case" : "Question"}</span>
              <span className="mono muted">{h.id}</span>
              <strong>{h.title}</strong>
              <span className="spacer" />
              <span className="tag">{domainShort(h.domain)}</span>
            </div>
            <p className="dim" style={{ margin: 0, fontSize: "var(--text-sm)" }}>{h.snippet}</p>
          </button>
        ))}
        {q.length >= 2 && hits.length === 0 && (
          <p className="muted">No matches. Try a different term.</p>
        )}
      </div>
    </div>
  );
}
