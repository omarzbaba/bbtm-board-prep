import { Route, Routes, useLocation } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useContent } from "./store/contentStore";
import { Dashboard } from "./pages/Dashboard";
import { Practice } from "./pages/Practice";
import { CaseMode } from "./pages/CaseMode";
import { Coverage } from "./pages/Coverage";
import { SearchPage } from "./pages/SearchPage";
import { Notebook } from "./pages/Notebook";
import { About } from "./pages/About";

export default function App() {
  const { loading, error, bundle } = useContent();
  const location = useLocation();

  return (
    <Layout>
      <div className="container page">
        {loading && (
          <div className="card pad center" style={{ padding: "var(--space-8)" }}>
            <div className="serif" style={{ fontSize: "1.4rem" }}>Loading study bank…</div>
            <p className="muted">Preparing questions, cases, and coverage.</p>
          </div>
        )}
        {error && !loading && (
          <div className="notice warn">Could not load content: {error}</div>
        )}
        {!loading && bundle && (
          <ErrorBoundary key={location.pathname}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/practice" element={<Practice />} />
              <Route path="/cases" element={<CaseMode />} />
              <Route path="/coverage" element={<Coverage />} />
              <Route path="/notebook" element={<Notebook />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/about" element={<About />} />
              <Route path="*" element={<Dashboard />} />
            </Routes>
          </ErrorBoundary>
        )}
      </div>
    </Layout>
  );
}
