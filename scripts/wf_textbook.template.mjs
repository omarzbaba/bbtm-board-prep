export const meta = {
  name: 'bbtm-expand-generate-audit',
  description: 'Expand the BB/TM board bank ~5x: grounded multi-angle questions + cases, adversarially audited',
  phases: [
    { title: 'Questions', detail: 'grounded multi-angle MCQs per entity + batched audit' },
    { title: 'Cases', detail: 'grounded teaching cases + audit' },
  ],
}

const INPUT = __INPUT__;
const ROOT = '/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank';
const DESIG = { C: 'Core/Foundational', AR: 'Advanced Resident', F: 'Fellow/Advanced Practitioner' };

const REF_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['source_id', 'supports'],
  properties: {
    source_id: { type: 'string' }, locator: { type: 'string' },
    supports: { type: 'string' }, confidence: { type: 'string', enum: ['high', 'moderate', 'low'] },
  },
};
const Q_ITEM = {
  type: 'object', additionalProperties: false,
  required: ['groundable', 'stem', 'options', 'correct_option_id', 'explanation_correct', 'option_rationales', 'source_references', 'support_confidence', 'difficulty'],
  properties: {
    groundable: { type: 'boolean', description: 'True only if the provided passages genuinely and substantively cover this topic. False = do not use; a placeholder was returned.' },
    stem: { type: 'string', minLength: 20 },
    options: { type: 'array', minItems: 4, maxItems: 5, items: { type: 'object', additionalProperties: false, required: ['id', 'text'], properties: { id: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E'] }, text: { type: 'string', minLength: 1 } } } },
    correct_option_id: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E'] },
    explanation_correct: { type: 'string', minLength: 25 },
    option_rationales: { type: 'array', minItems: 4, maxItems: 5, items: { type: 'object', additionalProperties: false, required: ['id', 'text'], properties: { id: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E'] }, text: { type: 'string', minLength: 5 } } } },
    teaching_point: { type: 'string' },
    difficulty: { type: 'string', enum: ['easy', 'moderate', 'hard'] },
    cognitive_level: { type: 'string', enum: ['recall', 'interpretation', 'application', 'analysis'] },
    source_references: { type: 'array', minItems: 1, items: REF_SCHEMA },
    support_confidence: { type: 'string', enum: ['high', 'moderate', 'low'] },
  },
};
const Q_GROUP_SCHEMA = { type: 'object', additionalProperties: false, required: ['questions'], properties: { questions: { type: 'array', minItems: 1, maxItems: 4, items: Q_ITEM } } };
const Q_AUDIT_GROUP_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdicts'],
  properties: { verdicts: { type: 'array', items: {
    type: 'object', additionalProperties: false,
    required: ['question_index', 'source_support', 'single_best_answer', 'answer_agrees', 'flags', 'severity', 'verdict_notes'],
    properties: {
      question_index: { type: 'integer' },
      source_support: { type: 'string', enum: ['pass', 'partial', 'uncertain', 'fail'] },
      single_best_answer: { type: 'boolean' },
      independent_answer: { type: 'string', enum: ['A', 'B', 'C', 'D', 'E', 'none'] },
      answer_agrees: { type: 'boolean' },
      flags: { type: 'array', items: { type: 'string', enum: ['unsupported-claim', 'ambiguous-stem', 'multiple-defensible-answers', 'weak-distractor', 'duplicate-coverage', 'blueprint-mismatch', 'overclaims-as-policy', 'numeric-value-unverified', 'too-esoteric-thin-source'] } },
      severity: { type: 'string', enum: ['none', 'low', 'medium', 'high'] },
      verdict_notes: { type: 'string' },
    },
  } } },
};
const CASE_GEN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['title', 'clinical_setup', 'findings', 'decision_points', 'teaching_explanation', 'pitfalls', 'source_references', 'support_confidence'],
  properties: {
    title: { type: 'string', minLength: 4 }, clinical_setup: { type: 'string', minLength: 40 },
    findings: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['label', 'value'], properties: { label: { type: 'string' }, value: { type: 'string' }, flag: { type: 'string', enum: ['normal', 'abnormal', 'critical', 'n/a'] } } } },
    decision_points: { type: 'array', minItems: 1, items: { type: 'object', additionalProperties: false, required: ['stage', 'prompt', 'answer', 'rationale'], properties: { stage: { type: 'integer' }, prompt: { type: 'string', minLength: 8 }, options: { type: 'array', items: { type: 'string' } }, answer: { type: 'string' }, rationale: { type: 'string', minLength: 10 } } } },
    answer_key: { type: 'string' }, teaching_explanation: { type: 'string', minLength: 40 },
    pitfalls: { type: 'array', minItems: 1, items: { type: 'string' } },
    difficulty: { type: 'string', enum: ['easy', 'moderate', 'hard'] },
    source_references: { type: 'array', minItems: 1, items: REF_SCHEMA },
    support_confidence: { type: 'string', enum: ['high', 'moderate', 'low'] },
  },
};
const CASE_AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['source_support', 'clinically_realistic', 'flags', 'severity', 'verdict_notes'],
  properties: {
    source_support: { type: 'string', enum: ['pass', 'partial', 'uncertain', 'fail'] },
    clinically_realistic: { type: 'boolean' },
    flags: { type: 'array', items: { type: 'string', enum: ['unsupported-claim', 'unrealistic-scenario', 'incorrect-answer-key', 'blueprint-mismatch', 'overclaims-as-policy', 'numeric-value-unverified', 'too-esoteric-thin-source', 'missing-decision-logic'] } },
    severity: { type: 'string', enum: ['none', 'low', 'medium', 'high'] },
    verdict_notes: { type: 'string' }, suggested_fix: { type: 'string' },
  },
};

function srcList(item) { return item.sources.map(s => `  - ${s.source_id}: ${ROOT}/${s.rel_path}`).join('\n'); }

function genQGroupPrompt(g) {
  return `You are an expert Blood Banking / Transfusion Medicine board-question writer creating ONE one-best-answer MCQ on a specific topic for a physician preparing for the ABPath BB/TM subspecialty exam.

TARGET TOPIC: ${g.entity}
Blueprint: ${g.topic_path} · Designation: ${g.designation} (${DESIG[g.designation] || g.designation})

GROUNDING SOURCE — Read this file with the Read tool. It contains RETRIEVED PASSAGES from authoritative reference textbooks (AABB Technical Manual; Harmening, Modern Blood Banking; AABB Standards). Each passage is headed with its citation, e.g. "[AABB Technical Manual, 20th ed., p.123]":
${srcList(g)}

CRITICAL — retrieval is imperfect: the passages were auto-selected and MAY include adjacent or unrelated topics.
- Use ONLY the sentences genuinely about "${g.entity}" to build the question.
- If, after reading, the passages do NOT substantively cover "${g.entity}" (only a passing mention, or they are about a different topic), set groundable=false and return a minimal placeholder question — do NOT fabricate from outside knowledge. It is correct and expected to decline when the passages don't cover the topic.

When the topic IS genuinely covered (groundable=true):
1. SOURCE-GROUNDED: every fact in the stem, the correct answer, and each distractor rationale must be supported by the on-topic passage text. Do NOT introduce facts, numbers, or thresholds not in the passages.
2. FORMAT: a focused clinical vignette or scenario stem ending in ONE clear lead-in; 4-5 options; exactly ONE best answer; plausible-but-wrong distractors.
3. Provide explanation_correct and an option_rationales entry for EVERY option.
4. CITATIONS: in source_references, cite the specific textbook + page from the passage header you used (put the page in "locator", e.g. "p.123"), with a short paraphrase (<=400 chars, your own words). No long verbatim quotes.
5. Educational board-prep only; not institutional policy. Set support_confidence honestly.

Return {questions:[...]} with exactly ${g.angles.length} item(s) via StructuredOutput.`;
}

function auditQGroupPrompt(g, qs) {
  return `You are a SKEPTICAL, adversarial BB/TM board-content auditor. FIND problems; do not rubber-stamp.

Independently Read these SAME approved sources with the Read tool:
${srcList(g)}

Blueprint topic: ${g.topic_path} (node ${g.blueprint_node_id}, ${g.designation}).

Below are ${qs.length} candidate question(s) as a JSON array (0-indexed):
${JSON.stringify(qs, null, 1)}

For EACH question (by 0-based question_index) verify:
1. SOURCE SUPPORT — is every asserted fact (stem, keyed answer, each distractor rationale) supported by these sources? Absent/contradicted/invented facts => fail or partial; only 'pass' if fully grounded.
2. SINGLE BEST ANSWER — independently pick the best answer from the sources (independent_answer); does it match the key (answer_agrees)? More than one defensible answer => single_best_answer=false.
3. QUALITY flags + severity.
Be strict; if unsure a fact is in the sources use uncertain/partial, not pass. Return {verdicts:[...]} with one verdict per question (question_index 0..${qs.length - 1}) via StructuredOutput.`;
}

function genCasePrompt(item) {
  return `You are an expert Blood Banking / Transfusion Medicine educator writing ONE realistic, staged TEACHING CASE for a physician preparing for the ABPath BB/TM subspecialty exam.

BLUEPRINT TOPIC: ${item.topic_path}
Blueprint node: ${item.blueprint_node_id} · Designation: ${item.designation} · Domain: ${item.domain}

APPROVED SOURCES — Read EACH file with the Read tool, fully, before writing. Ground everything ONLY in them:
${srcList(item)}

REQUIREMENTS: realistic clinical_setup + relevant labelled findings; 2-4 staged decision_points (each with the correct answer + a source-grounded rationale); answer_key; teaching_explanation; 1-4 pitfalls. SOURCE-GROUNDED — every clinical fact, lab pattern, and management step must come from the sources; do NOT invent numbers absent from them. Realistic illustrative demographics are fine. Educational only; cite source_references; set support_confidence honestly. Return via StructuredOutput.`;
}
function auditCasePrompt(item, c) {
  return `You are a SKEPTICAL BB/TM content auditor reviewing a teaching case. FIND problems.
Independently Read these SAME approved sources:
${srcList(item)}
Blueprint topic: ${item.topic_path} (${item.blueprint_node_id}, ${item.designation}).
CANDIDATE CASE (JSON):
${JSON.stringify(c, null, 1)}
Check: (1) SOURCE SUPPORT — is every clinical fact, lab pattern, decision, and pitfall supported? invented numbers/unsupported management => fail/partial. (2) clinically_realistic + internally consistent. (3) any wrong decision answer_key. Flag + set severity. Unsure => uncertain/partial. Return via StructuredOutput.`;
}

const OPTS = { agentType: 'general-purpose', model: 'sonnet' };

phase('Questions');
const qGroups = INPUT.questionGroups;
const totalPlanned = qGroups.reduce((n, g) => n + g.angles.length, 0);
log(`Questions: ${totalPlanned} across ${qGroups.length} entity groups`);
const qResults = await pipeline(
  qGroups,
  (g) => agent(genQGroupPrompt(g), { ...OPTS, label: `gen:${g.ids[0]}+`, phase: 'Questions', schema: Q_GROUP_SCHEMA })
    .then(r => (r && r.questions ? { g, questions: r.questions } : null)),
  (prev) => {
    if (!prev) return null;
    return agent(auditQGroupPrompt(prev.g, prev.questions), { ...OPTS, label: `audit:${prev.g.ids[0]}+`, phase: 'Questions', schema: Q_AUDIT_GROUP_SCHEMA })
      .then(a => ({ group: prev.g, questions: prev.questions, verdicts: (a && a.verdicts) || [] }));
  },
);

phase('Cases');
const cResults = await pipeline(
  INPUT.casePlan,
  (item) => agent(genCasePrompt(item), { ...OPTS, label: `gen:${item.id}`, phase: 'Cases', schema: CASE_GEN_SCHEMA })
    .then(c => (c ? { item, c } : null)),
  (prev) => {
    if (!prev) return null;
    return agent(auditCasePrompt(prev.item, prev.c), { ...OPTS, label: `audit:${prev.item.id}`, phase: 'Cases', schema: CASE_AUDIT_SCHEMA })
      .then(a => ({ item: prev.item, case: prev.c, audit: a }));
  },
);

const okQ = qResults.filter(Boolean);
const okC = cResults.filter(Boolean);
const totalQ = okQ.reduce((n, r) => n + r.questions.length, 0);
log(`Generated ${totalQ} questions across ${okQ.length} groups, ${okC.length} cases`);
return { questionGroups: okQ, cases: okC, counts: { questions: totalQ, groups: okQ.length, cases: okC.length } };
