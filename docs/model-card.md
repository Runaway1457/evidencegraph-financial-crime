# Model card — Investigation proposal layer

## Intended use

EvidenceGraph uses an agent behind a typed `InvestigatorAgent` port to propose
hypotheses for a trained financial-crime investigator. Agent output is advisory. It
cannot create evidence, change relationships, confirm findings, or bypass policy.

The default release ships an explainable deterministic baseline so the entire product
and eval suite can run without external model credentials. Model-backed adapters must
satisfy the same proposal contract and grounding gate before they can be enabled.

## Output contract

Every proposal must provide a non-empty title and rationale, a confidence in `[0, 1]`,
and a unique set of evidence IDs already present in the case ledger. The application
service validates the entire batch before one database write occurs.

## Human accountability

A proposal is persisted only as `PROPOSED`. The proposer and reviewer must differ.
OPA authorizes `finding.review`; the domain model and database independently enforce
the four-eyes rule.

## Known limitations

- The deterministic baseline detects connected two-hop relationship paths; it is not a
  suspicious-activity classifier.
- Confidence is a proposal attribute, not a calibrated probability of criminal conduct.
- The included fixtures are synthetic and cannot establish production precision/recall.
- Jurisdiction-specific reporting decisions remain the responsibility of authorized staff.

## Evaluation

`evals/grounding_cases.jsonl` exercises accepted and adversarial outputs. CI runs the
same production grounding gate and publishes `eval-results.json`. The initial suite
contains 10 cases and requires zero false accepts and zero false rejects.

## Release criteria for a model adapter

A model-backed adapter must add task-specific evals, prompt-injection fixtures, latency
and cost measurements, calibration analysis, trace redaction verification, and signed
approval from security and model-risk owners.
