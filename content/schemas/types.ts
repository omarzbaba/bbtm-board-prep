// Canonical TypeScript types for the BB/TM board-prep platform.
// Mirrors the JSON Schemas in this directory. Imported by the web app.

export type Designation = "C" | "AR" | "F";
export type Difficulty = "easy" | "moderate" | "hard";
export type Confidence = "high" | "moderate" | "low";
export type OptionId = "A" | "B" | "C" | "D" | "E";

export type CoverageStatus =
  | "covered"
  | "strong-partial"
  | "weak-partial"
  | "thin"
  | "uncertain"
  | "missing";

export interface SourceReference {
  source_id: string;
  source_type: "notebooklm" | "blueprint" | "reference-text";
  source_title?: string;
  locator?: string;
  supports: string;
  blueprint_node_id?: string;
  confidence?: Confidence;
}

export type ReviewStatus =
  | "machine-generated"
  | "auto-audited-pass"
  | "needs-human-review"
  | "human-approved"
  | "flagged-inaccurate"
  | "revised";

export interface ReviewState {
  status: ReviewStatus;
  source_support: "pass" | "partial" | "uncertain" | "fail";
  audit_flags?: string[];
  auditor?: string;
  audited_at?: string;
  notes?: string;
}

export interface QuestionOption {
  id: OptionId;
  text: string;
}

export interface BoardQuestion {
  id: string;
  domain: string;
  subdomain: string;
  blueprint_node_id: string;
  designation: Designation;
  difficulty: Difficulty;
  cognitive_level?: "recall" | "interpretation" | "application" | "analysis";
  stem: string;
  options: QuestionOption[];
  correct_option_id: OptionId;
  explanation_correct: string;
  option_explanations: Partial<Record<OptionId, string>>;
  teaching_point?: string;
  source_references: SourceReference[];
  support_confidence: Confidence;
  tags?: string[];
  learner_note?: string | null;
  review: ReviewState;
  created_at?: string;
  generator?: string;
}

export interface CaseFinding {
  label: string;
  value: string;
  flag?: "normal" | "abnormal" | "critical" | "n/a";
}

export interface CaseDecisionPoint {
  stage?: number;
  prompt: string;
  options?: string[];
  answer: string;
  rationale: string;
}

export interface TeachingCase {
  id: string;
  title: string;
  domains: string[];
  blueprint_node_ids: string[];
  designation?: Designation;
  difficulty?: Difficulty;
  clinical_setup: string;
  findings: CaseFinding[];
  decision_points: CaseDecisionPoint[];
  answer_key?: string;
  teaching_explanation: string;
  pitfalls: string[];
  source_references: SourceReference[];
  support_confidence: Confidence;
  tags?: string[];
  learner_note?: string | null;
  review: ReviewState;
  created_at?: string;
  generator?: string;
}

// ---- Blueprint ontology ----
export interface BlueprintNode {
  id: string;
  marker: string;
  title: string;
  designation: Designation | null;
  level: "section" | "letter" | "roman" | "arabic";
  children: BlueprintNode[];
}

// ---- Coverage ----
export interface CoverageNode {
  id: string;
  title: string;
  designation: Designation | null;
  section: string;
  section_title: string;
  level: string;
  is_leaf: boolean;
  status: CoverageStatus;
  anchor_phrase: string;
  anchor_source_hits: string[];
  best_support: number;
  source_confidence: number;
  supporting_sources: string[];
}

// ---- Per-learner runtime state ----
export interface AttemptState {
  seen: number;
  correct: number;
  last_choice?: string | null;
  last_result?: "correct" | "incorrect" | null;
  last_seen_at?: string | null;
  box?: number; // Leitner box 0-5
}

export interface CaseProgress {
  completed: boolean;
  revealed_stages: number[];
  last_seen_at?: string | null;
}

export interface LearnerState {
  version: 1;
  learner_id?: string;
  updated_at?: string;
  notes: Record<string, string>;
  weak_marks: Record<string, boolean>;
  attempts: Record<string, AttemptState>;
  case_progress?: Record<string, CaseProgress>;
}
