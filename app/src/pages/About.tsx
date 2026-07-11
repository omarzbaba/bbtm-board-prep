import { useState } from "react";
import { useContent } from "../store/contentStore";
import { useLearner } from "../store/learnerStore";

export function About() {
  const { bundle } = useContent();
  const { learnerId, changeLearnerId, resetAll, cloudEnabled, syncStatus } = useLearner();
  const [idInput, setIdInput] = useState(learnerId);
  const [confirmReset, setConfirmReset] = useState(false);

  return (
    <div className="stack gap-5" style={{ maxWidth: 720 }}>
      <h1 className="serif" style={{ fontSize: "var(--text-xl)" }}>About & settings</h1>

      <section className="card pad stack gap-3">
        <span className="eyebrow">How this bank is built</span>
        <p style={{ margin: 0 }}>
          Every question and case is generated <strong>only</strong> from approved sources — a NotebookLM study export
          plus the official ABPath BB/TM content specification — then independently audited for source support. Items
          carry a <em>source trace</em> so you can see what backs each answer. This is an educational board-prep aid,
          not clinical decision support or institutional policy.
        </p>
        <div className="row gap-4 wrap">
          <span className="tag">{bundle!.questions.length} questions</span>
          <span className="tag">{bundle!.cases.length} cases</span>
          {bundle!.meta.generated_at && <span className="tag">built {new Date(bundle!.meta.generated_at).toLocaleDateString()}</span>}
        </div>
      </section>

      <section className="card pad stack gap-3">
        <span className="eyebrow">Your progress</span>
        <p className="dim" style={{ margin: 0, fontSize: "var(--text-sm)" }}>
          {cloudEnabled
            ? `Progress, notes, and weak-marks sync to the cloud (status: ${syncStatus}) and are also kept on this device.`
            : "Progress, notes, and weak-marks are saved in this browser. They stay on this device."}
        </p>
        <div className="stack gap-2">
          <label className="eyebrow" htmlFor="lid">Study profile ID {cloudEnabled ? "(used for cloud sync)" : ""}</label>
          <div className="row gap-2 wrap">
            <input id="lid" className="input" style={{ maxWidth: 260 }} value={idInput}
              onChange={(e) => setIdInput(e.target.value)} />
            <button className="btn" onClick={() => changeLearnerId(idInput)} disabled={!idInput.trim() || idInput === learnerId}>
              Save ID
            </button>
          </div>
          {cloudEnabled && <p className="muted" style={{ fontSize: 11, margin: 0 }}>Use the same ID on another device to load your saved progress.</p>}
        </div>
      </section>

      <section className="card pad stack gap-3">
        <span className="eyebrow" style={{ color: "var(--bad)" }}>Danger zone</span>
        {!confirmReset ? (
          <button className="btn" onClick={() => setConfirmReset(true)}>Reset all my progress</button>
        ) : (
          <div className="row gap-2 wrap">
            <span className="dim" style={{ fontSize: "var(--text-sm)" }}>This clears notes, weak-marks, and attempts. Sure?</span>
            <button className="btn" style={{ borderColor: "var(--bad)", color: "var(--bad)" }} onClick={() => { resetAll(); setConfirmReset(false); }}>Yes, reset</button>
            <button className="btn ghost" onClick={() => setConfirmReset(false)}>Cancel</button>
          </div>
        )}
      </section>

      <p className="muted" style={{ fontSize: "var(--text-xs)" }}>
        Content may contain errors and is not a substitute for authoritative references or clinical judgment.
        Items flagged “needs human review” are shown with a caution banner.
      </p>
    </div>
  );
}
