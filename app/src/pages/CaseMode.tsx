import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useContent } from "../store/contentStore";
import { useLearner } from "../store/learnerStore";
import type { TeachingCase } from "../types";
import { DesignationBadge, Empty } from "../components/ui";
import { NoteEditor, SourceTrace, WeakStar } from "../components/ItemControls";
import { domainNumber, domainShort } from "../lib/util";

function CaseCard({ c, onOpen }: { c: TeachingCase; onOpen: () => void }) {
  const { state } = useLearner();
  const done = state.case_progress?.[c.id]?.completed;
  return (
    <button className="card card-hover pad stack gap-3" onClick={onOpen}
      style={{ textAlign: "left", cursor: "pointer", color: "inherit" }}>
      <div className="row gap-2 wrap">
        <DesignationBadge d={c.designation ?? null} />
        {c.domains.slice(0, 1).map((d) => <span key={d} className="tag">{domainShort(d)}</span>)}
        {c.difficulty && <span className="badge outline">{c.difficulty}</span>}
        <span className="spacer" />
        {done && <span className="badge c">✓ done</span>}
        {state.weak_marks[c.id] && <span style={{ color: "var(--gold)" }}>★</span>}
      </div>
      <strong className="serif" style={{ fontSize: "var(--text-md)" }}>{c.title}</strong>
      <p className="dim" style={{ fontSize: "var(--text-sm)", margin: 0, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
        {c.clinical_setup}
      </p>
      <span className="muted" style={{ fontSize: 12 }}>{c.decision_points.length} decision point{c.decision_points.length > 1 ? "s" : ""}</span>
    </button>
  );
}

function CaseView({ c, onBack }: { c: TeachingCase; onBack: () => void }) {
  const { markCaseStage } = useLearner();
  const [revealed, setRevealed] = useState<Set<number>>(new Set());
  const [showKey, setShowKey] = useState(false);

  const reveal = (stage: number) => {
    setRevealed((s) => new Set(s).add(stage));
    const done = c.decision_points.every((dp, i) => revealed.has(dp.stage ?? i + 1) || (dp.stage ?? i + 1) === stage);
    markCaseStage(c.id, stage, done);
  };

  return (
    <div className="stack gap-5">
      <button className="btn ghost sm" onClick={onBack} style={{ alignSelf: "flex-start" }}>← All cases</button>

      <div className="card pad stack gap-4">
        <div className="row gap-2 wrap">
          <span className="mono muted">{c.id}</span>
          <DesignationBadge d={c.designation ?? null} />
          {c.domains.map((d) => <span key={d} className="tag">{domainNumber(d)}. {domainShort(d)}</span>)}
          <span className="spacer" />
          <WeakStar itemId={c.id} />
        </div>
        <h1 className="serif" style={{ fontSize: "var(--text-xl)" }}>{c.title}</h1>
        <p style={{ margin: 0 }}>{c.clinical_setup}</p>

        {c.findings?.length > 0 && (
          <div className="panel stack gap-2">
            <span className="eyebrow">Findings</span>
            <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
              {c.findings.map((f, i) => (
                <div key={i} className="row gap-2" style={{ justifyContent: "space-between", padding: "3px 0", borderBottom: "1px dashed var(--border)" }}>
                  <span className="dim" style={{ fontSize: "var(--text-sm)" }}>{f.label}</span>
                  <span style={{ fontWeight: 600, fontSize: "var(--text-sm)", color: f.flag === "critical" ? "var(--bad)" : f.flag === "abnormal" ? "var(--warn)" : "var(--text)" }}>
                    {f.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Staged decision points */}
      <div className="stack gap-4">
        {c.decision_points.map((dp, i) => {
          const stage = dp.stage ?? i + 1;
          const open = revealed.has(stage);
          return (
            <div key={i} className="card pad stack gap-3">
              <div className="row gap-2">
                <span className="badge f">Step {stage}</span>
                <strong>{dp.prompt}</strong>
              </div>
              {dp.options && dp.options.length > 0 && (
                <ul className="stack gap-1" style={{ margin: 0, paddingLeft: "1.1rem" }}>
                  {dp.options.map((o, k) => <li key={k} className="dim" style={{ fontSize: "var(--text-sm)" }}>{o}</li>)}
                </ul>
              )}
              {open ? (
                <div className="panel correct-ex stack gap-1">
                  <span className="eyebrow" style={{ color: "var(--ok)" }}>Answer</span>
                  <strong>{dp.answer}</strong>
                  <p className="dim" style={{ margin: "2px 0 0", fontSize: "var(--text-sm)" }}>{dp.rationale}</p>
                </div>
              ) : (
                <button className="btn sm" style={{ alignSelf: "flex-start" }} onClick={() => reveal(stage)}>Reveal answer</button>
              )}
            </div>
          );
        })}
      </div>

      {/* Teaching + key */}
      <div className="card pad stack gap-3">
        <button className="row gap-2" onClick={() => setShowKey((s) => !s)}
          style={{ background: "none", border: "none", padding: 0, cursor: "pointer", color: "var(--text)" }}>
          <span className="eyebrow">▸ Teaching summary & pitfalls</span>
        </button>
        {showKey && (
          <>
            {c.answer_key && <div className="panel"><span className="eyebrow">Key pathway</span><p style={{ margin: "4px 0 0" }}>{c.answer_key}</p></div>}
            <p style={{ margin: 0 }}>{c.teaching_explanation}</p>
            {c.pitfalls?.length > 0 && (
              <div className="panel" style={{ borderLeft: "3px solid var(--warn)" }}>
                <span className="eyebrow" style={{ color: "var(--warn)" }}>Pitfalls / board traps</span>
                <ul style={{ margin: "6px 0 0", paddingLeft: "1.1rem" }}>
                  {c.pitfalls.map((p, i) => <li key={i} style={{ fontSize: "var(--text-sm)" }}>{p}</li>)}
                </ul>
              </div>
            )}
          </>
        )}
        <SourceTrace refs={c.source_references} confidence={c.support_confidence} />
        <NoteEditor itemId={c.id} />
      </div>
    </div>
  );
}

export function CaseMode() {
  const { bundle } = useContent();
  const cases = bundle!.cases;
  const [params, setParams] = useSearchParams();
  const [openId, setOpenId] = useState<string | null>(params.get("open"));
  const open = useMemo(() => cases.find((c) => c.id === openId) || null, [cases, openId]);

  // Deep-link support: /cases?open=C-003 (e.g. from the Notebook)
  useEffect(() => {
    const target = params.get("open");
    if (target && target !== openId) setOpenId(target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const close = () => {
    setOpenId(null);
    if (params.get("open")) { const n = new URLSearchParams(params); n.delete("open"); setParams(n, { replace: true }); }
  };

  if (cases.length === 0) {
    return <Empty title="No teaching cases yet" body="Cases will appear here once the content bank is built." />;
  }
  if (open) return <CaseView c={open} onBack={close} />;

  return (
    <div className="stack gap-4">
      <div className="stack gap-2">
        <h1 className="serif" style={{ fontSize: "var(--text-xl)" }}>Teaching cases</h1>
        <p className="dim" style={{ margin: 0 }}>Work through staged clinical decisions, then reveal the answer and teaching points.</p>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
        {cases.map((c) => <CaseCard key={c.id} c={c} onOpen={() => setOpenId(c.id)} />)}
      </div>
    </div>
  );
}
