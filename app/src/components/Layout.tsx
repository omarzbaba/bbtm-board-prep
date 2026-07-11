import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";
import { useLearner } from "../store/learnerStore";

const THEME_ICON: Record<string, string> = { light: "☀", dark: "☾", system: "◐" };

function SyncBadge() {
  const { syncStatus, cloudEnabled } = useLearner();
  if (!cloudEnabled) {
    return <span className="tag hide-sm" title="Progress is saved on this device">saved locally</span>;
  }
  const map: Record<string, [string, string]> = {
    syncing: ["syncing…", "var(--warn)"], synced: ["synced", "var(--ok)"],
    offline: ["offline", "var(--text-3)"], local: ["local", "var(--text-3)"],
  };
  const [label, color] = map[syncStatus] || ["", ""];
  return <span className="tag hide-sm" style={{ color }} title="Cloud sync status">● {label}</span>;
}

export function TopNav() {
  const { theme, cycle } = useTheme();
  return (
    <header className="topnav">
      <div className="container topnav-inner">
        <NavLink to="/" className="brand">
          <span className="glyph">🩸</span>
          <span>
            Blood Bank Board Prep
            <small>ABPath BB/TM · source-grounded</small>
          </span>
        </NavLink>
        <nav className="nav-links" aria-label="Primary">
          <NavLink to="/practice" className={({ isActive }) => (isActive ? "active" : "")}>Practice</NavLink>
          <NavLink to="/cases" className={({ isActive }) => (isActive ? "active" : "")}>Cases</NavLink>
          <NavLink to="/coverage" className={({ isActive }) => (isActive ? "active" : "")}>Coverage</NavLink>
          <NavLink to="/search" className={({ isActive }) => (isActive ? "active" : "")}>Search</NavLink>
        </nav>
        <div className="spacer" />
        <SyncBadge />
        <NavLink to="/about" className="btn ghost sm" title="About & settings" aria-label="About and settings">⚙</NavLink>
        <button className="btn ghost sm" onClick={cycle} title={`Theme: ${theme}`} aria-label="Toggle theme">
          {THEME_ICON[theme]}
        </button>
      </div>
    </header>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <TopNav />
      <main className="grow">{children}</main>
      <footer className="container" style={{ padding: "var(--space-6) var(--space-5)", color: "var(--text-3)", fontSize: "var(--text-xs)", borderTop: "1px solid var(--border)", marginTop: "var(--space-6)" }}>
        Educational board-preparation tool · content generated only from approved sources · not clinical decision support or institutional policy.
      </footer>
    </div>
  );
}
