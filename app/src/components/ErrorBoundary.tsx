import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

interface Props { children: ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Surface for debugging; a single bad item should never blank the whole app.
    console.error("[ErrorBoundary]", error.message, info.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (this.state.error) {
      return (
        <div className="card pad stack gap-3" style={{ margin: "var(--space-6) 0" }}>
          <h2 className="serif" style={{ fontSize: "var(--text-lg)" }}>Something went wrong on this screen</h2>
          <p className="dim" style={{ margin: 0 }}>Your saved progress is safe. Try another section, or reload.</p>
          <pre className="mono" style={{ whiteSpace: "pre-wrap", background: "var(--surface-2)", padding: "var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--text-xs)", overflowX: "auto" }}>
            {this.state.error.message}
            {"\n\n"}
            {(this.state.error.stack || "").split("\n").slice(0, 6).join("\n")}
          </pre>
          <div className="row gap-2">
            <button className="btn" onClick={this.reset}>Try again</button>
            <button className="btn ghost" onClick={() => location.reload()}>Reload app</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
