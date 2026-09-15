# Engineering standard

EvidenceGraph is evaluated by what the repository can demonstrate, not by how confidently it describes itself.

## Evidence before claims

Every material claim must resolve to one or more reviewable artifacts:

| Claim | Required evidence |
|---|---|
| “Implemented” | Executable runtime path and automated test |
| “Reliable” | Failure model, retry/idempotency behavior and operational signal |
| “Secure” | Named trust boundary, enforced control and negative test |
| “Production” | Deployment profile, secrets boundary, migration path, SLO and runbook |
| “AI quality” | Versioned evaluation data, acceptance criteria and measured result |

Planned adapters are labeled as planned. Synthetic data is labeled as synthetic. A UI fixture is never presented as a live control-plane response.

## Authorial voice

The repository communicates technical judgment directly.

- No “portfolio project,” “student project,” or self-awarded seniority language.
- No generic AI prose, unexplained framework lists or copied showcase structure.
- No fabricated stars, users, benchmarks, certifications or production deployments.
- No decorative diagrams that contradict the runtime.
- No footer that explains who the work is supposed to impress.

Authority should be visible in domain boundaries, invariants, migrations, tests, failure handling, measured trade-offs and restraint.

## Assistance policy

Automation and AI tools may accelerate research, implementation and review. Their output enters the workflow as an untrusted draft, under the same principle used by the product itself:

1. understand the proposed change;
2. verify it against repository state;
3. edit it into the system's vocabulary and architecture;
4. test positive, negative and failure paths;
5. accept personal accountability for the result.

Tool-generated filler, contradictory documentation and unreviewed code do not cross the quality gate.

## Release language

A release note states what changed, what was verified and what remains outside the supported boundary. It does not call the system “100% production ready.” Production suitability belongs to a named environment and threat model, not to a universal slogan.
