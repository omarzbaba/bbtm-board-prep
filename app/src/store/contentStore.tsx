import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { loadContent } from "../data/content";
import type { ContentBundle } from "../data/content";

interface ContentState {
  bundle: ContentBundle | null;
  loading: boolean;
  error: string | null;
}

const Ctx = createContext<ContentState>({ bundle: null, loading: true, error: null });

export function ContentProvider({ children }: { children: ReactNode }) {
  const [st, setSt] = useState<ContentState>({ bundle: null, loading: true, error: null });
  useEffect(() => {
    let cancel = false;
    loadContent()
      .then((bundle) => { if (!cancel) setSt({ bundle, loading: false, error: null }); })
      .catch((e) => { if (!cancel) setSt({ bundle: null, loading: false, error: String(e) }); });
    return () => { cancel = true; };
  }, []);
  return <Ctx.Provider value={st}>{children}</Ctx.Provider>;
}

export function useContent(): ContentState {
  return useContext(Ctx);
}
