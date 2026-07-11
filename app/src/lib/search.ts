import type { BoardQuestion, TeachingCase } from "../types";

export interface SearchHit {
  kind: "question" | "case";
  id: string;
  title: string;
  domain: string;
  snippet: string;
  score: number;
}

function norm(s: string): string {
  return s.toLowerCase();
}

function scoreText(hay: string, terms: string[]): number {
  const low = norm(hay);
  let score = 0;
  for (const t of terms) {
    let idx = low.indexOf(t);
    while (idx !== -1) {
      score += 1;
      idx = low.indexOf(t, idx + t.length);
    }
  }
  return score;
}

function snippetFor(text: string, terms: string[]): string {
  const low = norm(text);
  let pos = -1;
  for (const t of terms) {
    const i = low.indexOf(t);
    if (i !== -1 && (pos === -1 || i < pos)) pos = i;
  }
  if (pos === -1) return text.slice(0, 140);
  const start = Math.max(0, pos - 50);
  return (start > 0 ? "…" : "") + text.slice(start, start + 160) + "…";
}

export function search(query: string, questions: BoardQuestion[], cases: TeachingCase[]): SearchHit[] {
  const terms = norm(query).split(/\s+/).filter((t) => t.length >= 2);
  if (!terms.length) return [];
  const hits: SearchHit[] = [];

  for (const q of questions) {
    const blob = [q.stem, q.explanation_correct, q.teaching_point, q.subdomain, q.domain,
      ...q.options.map((o) => o.text), ...(q.tags || [])].filter(Boolean).join(" • ");
    const score = scoreText(blob, terms) + scoreText(q.subdomain + " " + q.domain, terms) * 2;
    if (score > 0) {
      hits.push({ kind: "question", id: q.id, title: q.subdomain || q.domain, domain: q.domain,
        snippet: snippetFor(q.stem, terms), score });
    }
  }
  for (const c of cases) {
    const blob = [c.title, c.clinical_setup, c.teaching_explanation, ...(c.pitfalls || []),
      ...c.domains, ...(c.tags || [])].filter(Boolean).join(" • ");
    const score = scoreText(blob, terms) + scoreText(c.title, terms) * 3;
    if (score > 0) {
      hits.push({ kind: "case", id: c.id, title: c.title, domain: c.domains[0] || "",
        snippet: snippetFor(c.clinical_setup, terms), score });
    }
  }
  return hits.sort((a, b) => b.score - a.score).slice(0, 40);
}
