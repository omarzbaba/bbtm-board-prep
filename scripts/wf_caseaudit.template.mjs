export const meta = {
  name: 'bbtm-case-audit',
  description: 'Adversarially audit the already-generated BB/TM teaching cases against their sources',
  phases: [{ title: 'Audit' }],
}

const INPUT = __INPUT__;
const ROOT = '/Users/omarbaba/Library/CloudStorage/OneDrive-Personal/tala blood bank';

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

function srcList(item) { return (item.sources || []).map(s => `  - ${s.source_id}: ${ROOT}/${s.rel_path}`).join('\n'); }
function auditCasePrompt(item, casePath) {
  return `You are a SKEPTICAL Blood Banking / Transfusion Medicine content auditor reviewing a teaching case. FIND problems.
Read the CANDIDATE CASE (JSON) with the Read tool at: ${ROOT}/${casePath}
Then independently Read these SAME approved sources with the Read tool:
${srcList(item)}
Blueprint topic: ${item.topic_path} (${item.blueprint_node_id}, ${item.designation}).
Check: (1) SOURCE SUPPORT — is every clinical fact, lab pattern, decision, and pitfall supported by these sources? invented numbers/unsupported management => fail/partial. (2) clinically_realistic + internally consistent. (3) any wrong decision answer_key. Flag + set severity. Unsure => uncertain/partial. Return the verdict via StructuredOutput.`;
}

phase('Audit');
const results = await parallel(INPUT.cases.map((rec) => () =>
  agent(auditCasePrompt(rec.item, rec.case_path), { agentType: 'general-purpose', model: 'sonnet', label: `audit:${rec.item.id}`, phase: 'Audit', schema: CASE_AUDIT_SCHEMA })
    .then((a) => (a ? { item: rec.item, case_id: rec.item.id, audit: a } : null))));

const ok = results.filter(Boolean);
log(`Audited ${ok.length}/${INPUT.cases.length} cases`);
return { cases: ok };
