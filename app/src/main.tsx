import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import { ContentProvider } from "./store/contentStore";
import { LearnerProvider } from "./store/learnerStore";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HashRouter>
      <ContentProvider>
        <LearnerProvider>
          <App />
        </LearnerProvider>
      </ContentProvider>
    </HashRouter>
  </StrictMode>,
);
