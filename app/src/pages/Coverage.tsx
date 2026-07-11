import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useContent } from "../store/contentStore";
import { Meter, StatusDot } from "../components/ui";
import { STATUS_LABEL, domainShort } from "../lib/util";

const STATUS_ORDER = ["covered", "strong-partial", "weak-partial", "thin", "uncertain", "missing"];

export function Coverage() {
  const { bundle } = useContent();
  const summaries = bundle!.coverageSummaries;
  const nodes = bundle!.coverage;
  const questions = bundle!.questions;
  const [openSection, setOpenSection] = useState<string | null>(null);

  const overall = useMemo(() => {
    const dist: Record<string, number> = {};
    let total = 0;
    for (const n of nodes) {
      if (!n.is_leaf) continue;
      dist[n.status] = (dist[n.status] || 0) + 1;
      total += 1;
    }
    const eligible = (dist["covered"] || 0) + (dist["strong-partial"] || 0);
    return { dist, total, eligible };
  }, [nodes]);

  const qByDomain = useMemo(() => {
    const m: Record<string, number> = {};
    for (const q of questions) {
      const sid = "S" + (q.domain.match(/^(\d+)/)?.[1] || "");
      m[sid] = (m[sid] || 0) + 1;
    }
    return m;
  }, [questions]);

  const sectionEntries = Object.entries(summaries).sort(
    (a, b) => parseInt(a[0].slice(1)) - parseInt(b[0].slice(1)),
  );

  return (
    <div className="stack gap-5">
      <div className="stack gap-2">
        <h1 className="serif" style={{ fontSize: "var(--text-xl)" }}>Blueprint coverage</h1>
        <p className="dim" style={{ margin: 0, maxWidth: 640 }}>
          How well your approved sources support each ABPath domain. This is a <strong>lexical-support</strong> signal,
          not a claim of correctness — thin and missing areas are surfaced honestly so you know where the sources are light.
        </p>
      </div>

      {/* Overall distribution */}
      <div className="card pad stack gap-3">
        <div className="row gap-3 wrap">
          <span className="eyebrow">Overall — {overall.total} leaf topics</span>
          <span className="spacer" />
          <span className="badge c">{overall.eligible} generation-eligible ({Math.round((overall.eligible / Math.max(1, overall.total)) * 100)}%)</span>
        </div>
        <div className="row" style={{ height: 14, borderRadius: 999, overflow: "hidden", border: "1px solid var(--border)" }}>
          {STATUS_ORDER.map((s) => {
            const w = ((overall.dist[s] || 0) / Math.max(1, overall.total)) * 100;
            if (w === 0) return null;
            return <span key={s} className={`st-${s}`} style={{ width: `${w}%` }} title={`${STATUS_LABEL[s]}: ${overall.dist[s]}`} />;
          })}
        </div>
        <div className="row gap-4 wrap">
          {STATUS_ORDER.filter((s) => overall.dist[s]).map((s) => (
            <span key={s} className="row gap-2" style={{ fontSize: "var(--text-xs)" }}>
              <StatusDot status={s} /> {STATUS_LABEL[s]} · {overall.dist[s]}
            </span>
          ))}
        </div>
      </div>

      {/* Per-domain */}
      <div className="stack gap-2">
        {sectionEntries.map(([sid, s]) => {
          const isOpen = openSection === sid;
          const thin = (s.status_distribution["thin"] || 0) + (s.status_distribution["missing"] || 0);
          return (
            <div key={sid} className="card">
              <button className="pad row gap-3 wrap" onClick={() => setOpenSection(isOpen ? null : sid)}
                style={{ width: "100%", background: "none", border: "none", cursor: "pointer", color: "inherit", textAlign: "left" }}>
                <span className="mono" style={{ color: "var(--accent)", fontWeight: 700, minWidth: 28 }}>{sid.slice(1)}</span>
                <strong style={{ minWidth: 180 }}>{domainShort(s.title)}</strong>
                <div style={{ flex: 1, minWidth: 160 }}><Meter value={s.coverage_score} /></div>
                <span className="badge outline">{Math.round(s.coverage_score * 100)}%</span>
                {qByDomain[sid] ? <span className="tag">{qByDomain[sid]} Q</span> : <span className="tag" style={{ opacity: 0.6 }}>0 Q</span>}
                {thin > 0 && <span className="badge f" title="thin or missing leaf topics">{thin} gap{thin > 1 ? "s" : ""}</span>}
                <span className="muted">{isOpen ? "▾" : "▸"}</span>
              </button>
              {isOpen && (
                <div className="pad" style={{ borderTop: "1px solid var(--border)" }}>
                  <SectionDetail sid={sid} nodes={nodes} coreScore={s.core_coverage_score} />
                </div>
              )}
            </div>
          );
        })}
      </div>
      <Link to="/practice" className="btn primary" style={{ alignSelf: "flex-start" }}>Practice these domains →</Link>
    </div>
  );
}

function SectionDetail({ sid, nodes, coreScore }: { sid: string; nodes: import("../types").CoverageNode[]; coreScore: number | null }) {
  const leaves = nodes.filter((n) => n.section === sid && n.is_leaf);
  const gaps = leaves.filter((n) => n.status === "thin" || n.status === "missing").slice(0, 30);
  const strong = leaves.filter((n) => n.status === "covered").slice(0, 12);
  return (
    <div className="stack gap-3">
      {coreScore !== null && (
        <div className="row gap-2"><span className="eyebrow">Core coverage</span><span className="badge c">{Math.round(coreScore * 100)}%</span></div>
      )}
      {strong.length > 0 && (
        <div className="stack gap-1">
          <span className="eyebrow" style={{ color: "var(--ok)" }}>Well-covered topics</span>
          <div className="row gap-2 wrap">
            {strong.map((n) => <span key={n.id} className="tag" style={{ color: "var(--ok)" }}>{n.title}</span>)}
          </div>
        </div>
      )}
      {gaps.length > 0 ? (
        <div className="stack gap-1">
          <span className="eyebrow" style={{ color: "var(--warn)" }}>Thin / missing (needs more source material)</span>
          <div className="row gap-2 wrap">
            {gaps.map((n) => (
              <span key={n.id} className="row gap-2" style={{ fontSize: "var(--text-xs)" }}>
                <StatusDot status={n.status} /> {n.title}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <span className="muted" style={{ fontSize: "var(--text-sm)" }}>No thin/missing leaves in this domain.</span>
      )}
    </div>
  );
}
