export const meta = {
  name: 'bbtm-generate-audit',
  description: 'Generate & adversarially audit pilot BB/TM board questions and cases, grounded only in approved sources',
  phases: [
    { title: 'Questions', detail: 'ground + adversarially audit ~78 one-best-answer MCQs' },
    { title: 'Cases', detail: 'ground + adversarially audit 20 staged teaching cases' },
  ],
}

// __INPUT__ is replaced with the embedded generation plan (question + case plans).
const INPUT = __INPUT__;

const DESIG = { C: 'Core/Foundational', AR: 'Advanced Resident', F: 'Fellow/Advanced Practitioner' };

// ---------------- Structured output schemas ----------------
const REF_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['source_id', 'supports'],
  properties: {
    source_id: { type: 'string' },
    locator: { type: 'string' },
    supports: { type: 'string', description: 'Short paraphrase (own words) of what this source supports. Not a verbatim quote.' },
    confidence: { type: 'string', enum: ['high', 'moderate', 'low'] },
  },
};

const Q_GEN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['stem', 'options', 'correct_option_id', 'explanation_correct', 'option_rationales', 'source_references', 'support_confidence', 'difficulty', 'groundable'],
  properties: {
    groundable: { type: 'boolean', description: 'False if the sources are too thin to write a fully grounded item; if false, still return a best-effort draft.' },
    stem: { type: 'string', minLength: 20 },
    options: {
      type: 'array', minItems: 4, maxItems: 5,
      items: { type: 'object', additionalProperties: false, required: ['id', 'text'],
        properties: { id: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E'] }, text: { type: 'string', minLength: 1 } } },
    },
    correct_option_id: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E'] },
    explanation_correct: { type: 'string', minLength: 25 },
    option_rationales: {
      type: 'array', minItems: 4, maxItems: 5,
      items: { type: 'object', additionalProperties: false, required: ['id', 'text'],
        properties: { id: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E'] }, text: { type: 'string', minLength: 5 } } },
    },
    teaching_point: { type: 'string' },
    difficulty: { type: 'string', enum: ['easy', 'moderate', 'hard'] },
    cognitive_level: { type: 'string', enum: ['recall', 'interpretation', 'application', 'analysis'] },
    source_references: { type: 'array', minItems: 1, items: REF_SCHEMA },
    support_confidence: { type: 'string', enum: ['high', 'moderate', 'low'] },
  },
};

const AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['source_support', 'single_best_answer', 'independent_answer', 'answer_agrees', 'flags', 'severity', 'verdict_notes'],
  properties: {
    source_support: { type: 'string', enum: ['pass', 'partial', 'uncertain', 'fail'] },
    single_best_answer: { type: 'boolean' },
    independent_answer: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E', 'none'] },
    answer_agrees: { type: 'boolean' },
    flags: { type: 'array', items: { type: 'string', enum: [
      'unsupported-claim', 'ambiguous-stem', 'multiple-defensible-answers', 'weak-distractor',
      'duplicate-coverage', 'blueprint-mismatch', 'overclaims-as-policy', 'numeric-value-unverified', 'too-esoteric-thin-source'] } },
    severity: { type: 'string', enum: ['none', 'low', 'medium', 'high'] },
    verdict_notes: { type: 'string' },
    suggested_fix: { type: 'string' },
  },
};

const CASE_GEN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'clinical_setup', 'findings', 'decision_points', 'teaching_explanation', 'pitfalls', 'source_references', 'support_confidence'],
  properties: {
    title: { type: 'string', minLength: 4 },
    clinical_setup: { type: 'string', minLength: 40 },
    findings: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['label', 'value'],
      properties: { label: { type: 'string' }, value: { type: 'string' }, flag: { type: 'string', enum: ['normal', 'abnormal', 'critical', 'n/a'] } } } },
    decision_points: { type: 'array', minItems: 1, items: { type: 'object', additionalProperties: false, required: ['stage', 'prompt', 'answer', 'rationale'],
      properties: { stage: { type: 'integer' }, prompt: { type: 'string', minLength: 8 }, options: { type: 'array', items: { type: 'string' } }, answer: { type: 'string' }, rationale: { type: 'string', minLength: 10 } } } },
    answer_key: { type: 'string' },
    teaching_explanation: { type: 'string', minLength: 40 },
    pitfalls: { type: 'array', minItems: 1, items: { type: 'string' } },
    difficulty: { type: 'string', enum: ['easy', 'moderate', 'hard'] },
    source_references: { type: 'array', minItems: 1, items: REF_SCHEMA },
    support_confidence: { type: 'string', enum: ['high', 'moderate', 'low'] },
  },
};

const CASE_AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['source_support', 'clinically_realistic', 'flags', 'severity', 'verdict_notes'],
  properties: {
    source_support: { type: 'string', enum: ['pass', 'partial', 'uncertain', 'fail'] },
    clinically_realistic: { type: 'boolean' },
    flags: { type: 'array', items: { type: 'string', enum: [
      'unsupported-claim', 'unrealistic-scenario', 'incorrect-answer-key', 'blueprint-mismatch',
      'overclaims-as-policy', 'numeric-value-unverified', 'too-esoteric-thin-source', 'missing-decision-logic'] } },
    severity: { type: 'string', enum: ['none', 'low', 'medium', 'high'] },
    verdict_notes: { type: 'string' },
    suggested_fix: { type: 'string' },
  },
};

// ---------------- Prompts ----------------
function sourceList(item) {
  return item.sources.map(s => `  - ${s.source_id}: ${s.abs_path}`).join('\n');
}

function genQuestionPrompt(item) {
  return `You are an expert Blood Banking / Transfusion Medicine board-question writer creating ONE one-best-answer multiple-choice question for a physician preparing for the ABPath BB/TM subspecialty exam.

BLUEPRINT TOPIC: ${item.topic_path}
Blueprint node: ${item.blueprint_node_id} · Designation: ${item.designation} (${DESIG[item.designation] || item.designation})
Domain: ${item.domain}

APPROVED SOURCES — Read EACH of these files with the Read tool, fully, before writing. Ground EVERY factual assertion ONLY in them:
${sourceList(item)}

STRICT RULES:
1. SOURCE-GROUNDED: Every fact in the stem, the correct answer, and each distractor rationale must be supported by the approved sources above. Do NOT add facts, numeric thresholds, or values that are not in the sources. If the sources lack a specific number, do not invent one — write around it.
2. FORMAT: One-best-answer. A focused clinical vignette or scenario stem ending in ONE clear lead-in question. 4-5 options, exactly ONE best answer. Distractors must be plausible-but-wrong — prefer the "board traps / distractors" the sources call out.
3. EXPLANATIONS: Give explanation_correct, and an option_rationales entry for EVERY option (why the answer is right / why each distractor is wrong).
4. CITATIONS: In source_references cite the actual source_id(s) you used, each with a short paraphrase (your own words, <= 400 chars) of what it supports. Never copy long verbatim text (max 15 words if you must quote).
5. FRAMING: Educational board-prep only. Do NOT present anything as institutional policy.
6. Prefer interpretation/application over rote recall. Set support_confidence honestly (high only if the sources fully and directly support the item). If the sources are too thin for a solid item, set groundable=false but still return your best draft.

Return the question via the StructuredOutput tool.`;
}

function auditQuestionPrompt(item, q) {
  return `You are a SKEPTICAL, adversarial Blood Banking / Transfusion Medicine board-content auditor. Your job is to FIND problems, not to rubber-stamp.

Independently Read these SAME approved sources with the Read tool:
${sourceList(item)}

Blueprint topic: ${item.topic_path} (node ${item.blueprint_node_id}, ${item.designation}).

CANDIDATE QUESTION (JSON):
${JSON.stringify(q, null, 1)}

Audit rigorously:
1. SOURCE SUPPORT — Is every asserted fact (stem premises, the keyed correct answer, and each distractor rationale) actually supported by these approved sources? If a key fact is absent from the sources, contradicts them, or is an invented number/threshold, mark source_support = fail (or partial if mostly supported). Only 'pass' if fully grounded.
2. SINGLE BEST ANSWER — Independently decide the best answer FROM THE SOURCES (independent_answer). Does it match correct_option_id (answer_agrees)? Is there more than one defensible answer (single_best_answer=false)?
3. QUALITY — flag: ambiguous stem, weak/implausible distractors, blueprint mismatch, overclaiming as policy, unverified numeric values, or too-esoteric/thin sourcing.

Be strict: if you are unsure whether a fact is in the sources, use source_support = uncertain or partial, NOT pass. Return the verdict via StructuredOutput.`;
}

function genCasePrompt(item) {
  return `You are an expert Blood Banking / Transfusion Medicine educator writing ONE realistic, staged TEACHING CASE for a physician preparing for the ABPath BB/TM subspecialty exam.

BLUEPRINT TOPIC: ${item.topic_path}
Blueprint node: ${item.blueprint_node_id} · Designation: ${item.designation} · Domain: ${item.domain}

APPROVED SOURCES — Read EACH file with the Read tool, fully, before writing. Ground everything ONLY in them:
${sourceList(item)}

REQUIREMENTS:
- A realistic clinical_setup (patient presentation) and relevant laboratory/transfusion findings (as labelled label/value pairs; mark flag normal/abnormal/critical).
- 2-4 staged decision_points (stage 1,2,3...): each a prompt the learner reasons through, with the correct answer and a source-grounded rationale. This is the case's teaching spine.
- answer_key (the correct overall pathway), a teaching_explanation, and 1-4 pitfalls (board traps).
- SOURCE-GROUNDED: every clinical fact, lab pattern, and management step must come from the approved sources. Do NOT invent numeric values not in the sources. Realistic illustrative patient demographics are fine, but the medicine must be source-backed.
- Educational framing only; not institutional policy. Cite source_references (source_id + short paraphrase). Set support_confidence honestly.

Return via the StructuredOutput tool.`;
}

function auditCasePrompt(item, c) {
  return `You are a SKEPTICAL Blood Banking / Transfusion Medicine content auditor reviewing a teaching case. FIND problems.

Independently Read these SAME approved sources:
${sourceList(item)}

Blueprint topic: ${item.topic_path} (${item.blueprint_node_id}, ${item.designation}).

CANDIDATE CASE (JSON):
${JSON.stringify(c, null, 1)}

Check: (1) SOURCE SUPPORT — is every clinical fact, lab pattern, decision, and pitfall supported by the sources? Invented numbers or unsupported management = fail/partial. (2) Is the scenario clinically realistic and internally consistent (clinically_realistic)? (3) Is any decision-point answer_key actually wrong per the sources? Flag issues and set severity. Be strict; unsure => uncertain/partial. Return via StructuredOutput.`;
}

// ---------------- Run ----------------
const AGENT_OPTS = { agentType: 'general-purpose', model: 'sonnet' };

phase('Questions');
const questionResults = await pipeline(
  INPUT.questionPlan,
  (item) => agent(genQuestionPrompt(item), { ...AGENT_OPTS, label: `gen:${item.id}`, phase: 'Questions', schema: Q_GEN_SCHEMA })
    .then(q => (q ? { item, q } : null)),
  (prev) => {
    if (!prev) return null;
    return agent(auditQuestionPrompt(prev.item, prev.q), { ...AGENT_OPTS, label: `audit:${prev.item.id}`, phase: 'Questions', schema: AUDIT_SCHEMA })
      .then(a => ({ item: prev.item, question: prev.q, audit: a }));
  },
);

phase('Cases');
const caseResults = await pipeline(
  INPUT.casePlan,
  (item) => agent(genCasePrompt(item), { ...AGENT_OPTS, label: `gen:${item.id}`, phase: 'Cases', schema: CASE_GEN_SCHEMA })
    .then(c => (c ? { item, c } : null)),
  (prev) => {
    if (!prev) return null;
    return agent(auditCasePrompt(prev.item, prev.c), { ...AGENT_OPTS, label: `audit:${prev.item.id}`, phase: 'Cases', schema: CASE_AUDIT_SCHEMA })
      .then(a => ({ item: prev.item, case: prev.c, audit: a }));
  },
);

const okQ = questionResults.filter(Boolean);
const okC = caseResults.filter(Boolean);
log(`Generated+audited ${okQ.length}/${INPUT.questionPlan.length} questions, ${okC.length}/${INPUT.casePlan.length} cases`);

return {
  questions: okQ,
  cases: okC,
  summary: {
    questions_total: okQ.length,
    questions_pass: okQ.filter(r => r.audit && (r.audit.source_support === 'pass' || r.audit.source_support === 'partial') && r.audit.answer_agrees && r.audit.single_best_answer).length,
    cases_total: okC.length,
    cases_pass: okC.filter(r => r.audit && (r.audit.source_support === 'pass' || r.audit.source_support === 'partial') && r.audit.clinically_realistic).length,
  },
};
