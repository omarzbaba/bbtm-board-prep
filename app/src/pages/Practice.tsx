import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useContent } from "../store/contentStore";
import { useLearner } from "../store/learnerStore";
import type { BoardQuestion } from "../types";
import { DesignationBadge, Empty } from "../components/ui";
import { NoteEditor, SourceTrace, WeakStar } from "../components/ItemControls";
import { domainNumber, domainShort } from "../lib/util";

export function Practice() {
  const { bundle } = useContent();
  const { state, recordAttempt } = useLearner();
  const [params, setParams] = useSearchParams();
  const questions = bundle!.questions;

  const domainFilter = params.get("domain") || "";
  const difficulty = params.get("difficulty") || "";
  const weakOnly = params.get("weak") === "1";
  const unseenOnly = params.get("unseen") === "1";
  const focusId = params.get("focus") || "";

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next, { replace: true });
  };

  const domains = useMemo(
    () => [...new Set(questions.map((q) => q.domain))].sort((a, b) => domainNumber(a) - domainNumber(b)),
    [questions],
  );

  const pool = useMemo(() => {
    if (focusId) {
      const one = questions.filter((q) => q.id === focusId);
      if (one.length) return one;
    }
    let qs = questions.filter((q) => {
      if (domainFilter && q.domain !== domainFilter) return false;
      if (difficulty && q.difficulty !== difficulty) return false;
      if (weakOnly && !state.weak_marks[q.id]) return false;
      if (unseenOnly && state.attempts[q.id]) return false;
      return true;
    });
    // order: unseen first, then weak, then by lowest Leitner box (spaced)
    qs = [...qs].sort((a, b) => {
      const aa = state.attempts[a.id], ba = state.attempts[b.id];
      const aScore = (aa ? 1 : 0) + (state.weak_marks[a.id] ? -0.5 : 0) + (aa?.box || 0) * 0.1;
      const bScore = (ba ? 1 : 0) + (state.weak_marks[b.id] ? -0.5 : 0) + (ba?.box || 0) * 0.1;
      return aScore - bScore;
    });
    return qs;
  }, [questions, domainFilter, difficulty, weakOnly, unseenOnly, state]);

  const [idx, setIdx] = useState(0);
  const [chosen, setChosen] = useState<string | null>(null);
  useEffect(() => { setIdx(0); setChosen(null); }, [domainFilter, difficulty, weakOnly, unseenOnly, focusId]);

  const q: BoardQuestion | undefined = pool[idx];
  // Options are pre-ordered A..E with a de-biased correct position at bank-build
  // time (see scripts/optnorm.py), so display them exactly as stored.
  const options = q ? q.options : [];

  if (pool.length === 0) {
    return <Empty title="No questions match these filters" body="Try clearing a filter or turning off weak / unseen only." />;
  }

  const answered = chosen !== null;
  const onChoose = (id: string) => {
    if (answered) return;
    setChosen(id);
    recordAttempt(q!.id, id, id === q!.correct_option_id);
  };
  const next = () => {
    setChosen(null);
    setIdx((i) => (i + 1) % pool.length);
  };

  const rationaleFor = (oid: string) => q!.option_explanations?.[oid as keyof typeof q.option_explanations];

  const focused = !!focusId && pool.length === 1 && pool[0].id === focusId;

  return (
    <div className="stack gap-5">
      {focused && (
        <div className="notice row gap-2 wrap">
          <span>📓 Viewing a single question from your notebook.</span>
          <span className="spacer" />
          <button className="btn ghost sm" onClick={() => setParam("focus", "")}>Clear · practice all →</button>
        </div>
      )}
      {/* Filter bar */}
      <div className="card pad row gap-3 wrap">
        <select className="select" style={{ width: "auto", minWidth: 180 }} value={domainFilter}
          onChange={(e) => setParam("domain", e.target.value)} aria-label="Domain filter">
          <option value="">All domains</option>
          {domains.map((d) => <option key={d} value={d}>{domainNumber(d)}. {domainShort(d)}</option>)}
        </select>
        <select className="select" style={{ width: "auto" }} value={difficulty}
          onChange={(e) => setParam("difficulty", e.target.value)} aria-label="Difficulty filter">
          <option value="">Any difficulty</option>
          <option value="easy">Easy</option>
          <option value="moderate">Moderate</option>
          <option value="hard">Hard</option>
        </select>
        <button className={`chip ${weakOnly ? "on" : ""}`} onClick={() => setParam("weak", weakOnly ? "" : "1")}>★ Weak only</button>
        <button className={`chip ${unseenOnly ? "on" : ""}`} onClick={() => setParam("unseen", unseenOnly ? "" : "1")}>◇ Unseen only</button>
        <span className="spacer" />
        <span className="muted" style={{ fontSize: "var(--text-sm)" }}>{idx + 1} / {pool.length}</span>
      </div>

      {/* Question */}
      <div className="card pad stack gap-4">
        <div className="row gap-2 wrap">
          <span className="mono muted">{q.id}</span>
          <DesignationBadge d={q.designation} />
          <span className="tag">{domainNumber(q.domain)}. {domainShort(q.domain)}</span>
          {q.subdomain && <span className="tag">{q.subdomain}</span>}
          {q.difficulty && <span className="badge outline">{q.difficulty}</span>}
          <span className="spacer" />
          <WeakStar itemId={q.id} />
        </div>

        <p className="serif" style={{ fontSize: "var(--text-md)", lineHeight: 1.55 }}>{q.stem}</p>

        <div className="stack gap-2">
          {options.map((o) => {
            const isCorrect = o.id === q.correct_option_id;
            const isChosen = o.id === chosen;
            let cls = "opt";
            if (answered) {
              if (isCorrect) cls += " correct";
              else if (isChosen) cls += " chosen-wrong";
              else cls += " dimmed";
            }
            return (
              <button key={o.id} className={cls} disabled={answered} onClick={() => onChoose(o.id)}>
                <span className="key">{o.id}</span>
                <span style={{ paddingTop: 2 }}>{o.text}</span>
                {answered && isCorrect && <span style={{ marginLeft: "auto", color: "var(--ok)" }}>✓</span>}
                {answered && isChosen && !isCorrect && <span style={{ marginLeft: "auto", color: "var(--bad)" }}>✗</span>}
              </button>
            );
          })}
        </div>

        {answered && (
          <div className="stack gap-4" style={{ marginTop: 2 }}>
            <div className="panel correct-ex stack gap-2">
              <span className="eyebrow" style={{ color: "var(--ok)" }}>
                {chosen === q.correct_option_id ? "✓ Correct" : `Answer: ${q.correct_option_id}`}
              </span>
              <p style={{ margin: 0 }}>{q.explanation_correct}</p>
              {q.teaching_point && (
                <p className="dim" style={{ margin: "4px 0 0", fontStyle: "italic" }}>Pearl: {q.teaching_point}</p>
              )}
            </div>

            {q.option_explanations && Object.keys(q.option_explanations).length > 0 && (
              <div className="panel stack gap-2">
                <span className="eyebrow">Why the other options are wrong</span>
                {options.filter((o) => o.id !== q.correct_option_id && rationaleFor(o.id)).map((o) => (
                  <div key={o.id} style={{ fontSize: "var(--text-sm)" }}>
                    <strong className="mono">{o.id}.</strong> <span className="dim">{rationaleFor(o.id)}</span>
                  </div>
                ))}
              </div>
            )}

            <SourceTrace refs={q.source_references} confidence={q.support_confidence} />

            {q.review?.status === "needs-human-review" && (
              <div className="notice warn">This item is flagged for human review — treat with extra caution.</div>
            )}

            <div className="row gap-3 wrap">
              <NoteEditor itemId={q.id} />
              <span className="spacer" />
              <button className="btn primary" onClick={next}>Next question →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
