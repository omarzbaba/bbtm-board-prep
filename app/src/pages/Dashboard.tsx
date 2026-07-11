import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useContent } from "../store/contentStore";
import { useLearner } from "../store/learnerStore";
import { ProgressRing, Stat } from "../components/ui";
import { domainNumber, domainShort, accuracy } from "../lib/util";

export function Dashboard() {
  const { bundle } = useContent();
  const { state } = useLearner();
  const questions = bundle!.questions;
  const cases = bundle!.cases;

  const stats = useMemo(() => {
    const ids = new Set(questions.map((q) => q.id));
    let seen = 0, correct = 0, attemptedUnique = 0;
    for (const [qid, a] of Object.entries(state.attempts)) {
      if (!ids.has(qid)) continue;
      attemptedUnique += 1;
      seen += a.seen || 0;
      correct += a.correct || 0;
    }
    const weak = Object.keys(state.weak_marks).filter((k) => k.startsWith("Q-") || k.startsWith("C-")).length;
    const notes = Object.keys(state.notes).length;
    const casesDone = Object.values(state.case_progress || {}).filter((c) => c.completed).length;
    return {
      attemptedUnique, seen, correct, weak, notes, casesDone,
      accuracy: accuracy(seen, correct),
      coverage: questions.length ? attemptedUnique / questions.length : 0,
    };
  }, [questions, state]);

  const domains = useMemo(() => {
    const map = new Map<string, { domain: string; total: number; attempted: number; correct: number; seen: number }>();
    for (const q of questions) {
      const d = map.get(q.domain) || { domain: q.domain, total: 0, attempted: 0, correct: 0, seen: 0 };
      d.total += 1;
      const a = state.attempts[q.id];
      if (a) { d.attempted += 1; d.correct += a.correct || 0; d.seen += a.seen || 0; }
      map.set(q.domain, d);
    }
    return [...map.values()].sort((a, b) => domainNumber(a.domain) - domainNumber(b.domain));
  }, [questions, state]);

  return (
    <div className="stack gap-6">
      {/* Hero */}
      <section className="card pad" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "var(--space-5)", alignItems: "center", background: "linear-gradient(120deg, var(--surface), var(--surface-2))" }}>
        <div className="stack gap-3">
          <span className="eyebrow">Welcome back</span>
          <h1 className="serif" style={{ fontSize: "var(--text-2xl)" }}>Your board-prep bench</h1>
          <p className="dim" style={{ maxWidth: 560 }}>
            {questions.length} source-grounded questions and {cases.length} teaching cases across the ABPath
            Blood Banking / Transfusion Medicine blueprint. Every item traces back to your approved sources.
          </p>
          <div className="row gap-3 wrap" style={{ marginTop: 4 }}>
            <Link to="/practice" className="btn primary">Start practice →</Link>
            <Link to="/cases" className="btn">Work a case</Link>
            {stats.weak > 0 && <Link to="/practice?weak=1" className="btn ghost">★ {stats.weak} weak item{stats.weak > 1 ? "s" : ""}</Link>}
          </div>
        </div>
        <ProgressRing value={stats.coverage} size={120} stroke={11} label="attempted" />
      </section>

      {/* Stat strip */}
      <section className="card pad">
        <div className="row wrap" style={{ gap: "var(--space-6)", justifyContent: "space-between" }}>
          <Stat value={stats.attemptedUnique + "/" + questions.length} label="Questions attempted" />
          <Stat value={stats.seen ? Math.round(stats.accuracy * 100) + "%" : "—"} label="Accuracy" accent={stats.accuracy >= 0.7 ? "var(--ok)" : stats.accuracy >= 0.5 ? "var(--warn)" : stats.seen ? "var(--bad)" : undefined} />
          <Stat value={stats.casesDone + "/" + cases.length} label="Cases completed" />
          <Stat value={stats.weak} label="Weak items" accent={stats.weak ? "var(--gold)" : undefined} />
          <Stat value={stats.notes} label="Notes written" />
        </div>
      </section>

      {/* Domains */}
      <section className="stack gap-3">
        <div className="row gap-3">
          <h2 className="serif" style={{ fontSize: "var(--text-lg)" }}>Practice by domain</h2>
          <span className="spacer" />
          <Link to="/coverage" className="btn ghost sm">View blueprint coverage →</Link>
        </div>
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))" }}>
          {domains.map((d) => {
            const acc = accuracy(d.seen, d.correct);
            return (
              <Link key={d.domain} to={`/practice?domain=${encodeURIComponent(d.domain)}`}
                className="card card-hover pad stack gap-3" style={{ textDecoration: "none", color: "inherit" }}>
                <div className="row gap-2">
                  <span className="mono" style={{ color: "var(--accent)", fontWeight: 700 }}>{domainNumber(d.domain)}</span>
                  <strong style={{ fontSize: "var(--text-base)" }}>{domainShort(d.domain)}</strong>
                </div>
                <div className="row gap-2" style={{ marginTop: "auto" }}>
                  <span className="muted" style={{ fontSize: "var(--text-sm)" }}>{d.attempted}/{d.total} done</span>
                  <span className="spacer" />
                  {d.seen > 0 && (
                    <span className="badge outline" style={{ color: acc >= 0.7 ? "var(--ok)" : acc >= 0.5 ? "var(--warn)" : "var(--bad)" }}>
                      {Math.round(acc * 100)}%
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
