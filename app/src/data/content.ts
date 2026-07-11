// Loads the source-grounded content bundle (questions, cases, blueprint, coverage)
// from static JSON under public/content/. All content is generated offline by the
// pipeline; the app is read-only over it.
import type { BoardQuestion, TeachingCase, BlueprintNode, CoverageNode } from "../types";

export interface ContentMeta {
  generated_at?: string;
  question_count: number;
  case_count: number;
  build?: string;
}

export interface ContentBundle {
  questions: BoardQuestion[];
  cases: TeachingCase[];
  blueprint: BlueprintNode[];
  coverage: CoverageNode[];
  coverageSummaries: Record<string, CoverageSectionSummary>;
  meta: ContentMeta;
}

export interface CoverageSectionSummary {
  title: string;
  leaf_count: number;
  coverage_score: number;
  core_leaf_count: number;
  core_coverage_score: number | null;
  status_distribution: Record<string, number>;
}

const base = import.meta.env.BASE_URL || "/";

async function getJSON<T>(file: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${base}content/${file}`, { cache: "no-cache" });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export async function loadContent(): Promise<ContentBundle> {
  const [questions, cases, blueprint, coverageDoc, meta] = await Promise.all([
    getJSON<{ questions: BoardQuestion[] }>("questions_pilot.json", { questions: [] }),
    getJSON<{ cases: TeachingCase[] }>("cases_pilot.json", { cases: [] }),
    getJSON<{ sections: BlueprintNode[] }>("blueprint_ontology.json", { sections: [] }),
    getJSON<{ nodes: CoverageNode[]; section_summaries: Record<string, CoverageSectionSummary> }>(
      "coverage_matrix.json",
      { nodes: [], section_summaries: {} },
    ),
    getJSON<ContentMeta>("meta.json", { question_count: 0, case_count: 0 }),
  ]);

  return {
    questions: questions.questions ?? [],
    cases: cases.cases ?? [],
    blueprint: blueprint.sections ?? [],
    coverage: coverageDoc.nodes ?? [],
    coverageSummaries: coverageDoc.section_summaries ?? {},
    meta,
  };
}

// ---- Derived helpers ----
export function domainList(questions: BoardQuestion[], cases: TeachingCase[]): string[] {
  const set = new Set<string>();
  questions.forEach((q) => set.add(q.domain));
  cases.forEach((c) => c.domains.forEach((d) => set.add(d)));
  return [...set].sort((a, b) => parseInt(a) - parseInt(b));
}
