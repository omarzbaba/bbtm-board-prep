import type { Designation } from "../types";
import { DESIGNATION_CLASS, DESIGNATION_LABEL, STATUS_LABEL } from "../lib/util";

export function DesignationBadge({ d, full = false }: { d: Designation | null; full?: boolean }) {
  if (!d) return null;
  return (
    <span className={`badge ${DESIGNATION_CLASS[d]}`} title={DESIGNATION_LABEL[d]}>
      {full ? DESIGNATION_LABEL[d] : d}
    </span>
  );
}

export function StatusDot({ status, withLabel = false }: { status: string; withLabel?: boolean }) {
  return (
    <span className="row gap-2" style={{ display: "inline-flex" }}>
      <span className={`dot st-${status}`} />
      {withLabel && <span className="dim" style={{ fontSize: "var(--text-xs)" }}>{STATUS_LABEL[status] || status}</span>}
    </span>
  );
}

export function ProgressRing({ value, size = 76, stroke = 8, label }: { value: number; size?: number; stroke?: number; label?: string }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(1, value)));
  return (
    <div style={{ position: "relative", width: size, height: size, flex: "0 0 auto" }}>
      <svg className="ring" width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--surface-2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--accent)" strokeWidth={stroke}
          strokeDasharray={c} strokeDashoffset={off} style={{ transition: "stroke-dashoffset 500ms var(--ease)" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", textAlign: "center", lineHeight: 1 }}>
        <div>
          <strong style={{ fontSize: size > 60 ? "1.15rem" : "0.9rem" }}>{Math.round(value * 100)}%</strong>
          {label && <div className="muted" style={{ fontSize: 10 }}>{label}</div>}
        </div>
      </div>
    </div>
  );
}

export function Meter({ value }: { value: number }) {
  return (
    <div className="meter" role="progressbar" aria-valuenow={Math.round(value * 100)} aria-valuemin={0} aria-valuemax={100}>
      <span style={{ width: `${Math.max(3, Math.min(100, value * 100))}%` }} />
    </div>
  );
}

export function Stat({ value, label, accent }: { value: React.ReactNode; label: string; accent?: string }) {
  return (
    <div className="stack" style={{ gap: 2 }}>
      <strong style={{ fontSize: "var(--text-xl)", color: accent || "var(--text)", fontFamily: "var(--font-serif)" }}>{value}</strong>
      <span className="eyebrow">{label}</span>
    </div>
  );
}

export function Empty({ title, body }: { title: string; body?: string }) {
  return (
    <div className="card pad center stack gap-2" style={{ padding: "var(--space-8)" }}>
      <div style={{ fontSize: "2rem", opacity: 0.5 }}>🩸</div>
      <h3 className="serif">{title}</h3>
      {body && <p className="muted" style={{ maxWidth: 460, margin: "0 auto" }}>{body}</p>}
    </div>
  );
}
