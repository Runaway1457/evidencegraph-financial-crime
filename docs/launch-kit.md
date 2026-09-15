# EvidenceGraph launch kit

Use the current CI-generated image at `docs/assets/investigation-workbench.webp`. Do not replace verified metrics with estimated numbers. Publish only after the release branch is merged and the repository visibility matches the intended audience.

## LinkedIn — Portuguese launch post

**Eu não queria construir mais um chatbot de portfólio.**

Queria responder uma pergunta mais difícil: como projetar IA para investigação financeira quando cada conclusão precisa ser provada, reproduzida e revisada?

Foi daí que nasceu o **EvidenceGraph Financial Crime** — uma plataforma evidence-first que transforma registros financeiros sintéticos em um grafo investigativo auditável.

O princípio central é simples:

**o modelo de linguagem não é a fonte da verdade.**

A cadeia de confiança é:

Evidence → Graph Path → Hypothesis → Policy + Grounding → Independent Review → Finding

O sistema reúne:

• domínio e API em Python/FastAPI  
• PostgreSQL + migrations Alembic  
• relações e findings obrigatoriamente vinculados a evidências do mesmo caso  
• hashes SHA-256, audit trail e chain of custody  
• baseline investigativo determinístico  
• output de agente tratado como input não confiável  
• grounding gate contra citações inexistentes  
• OPA/Rego para autorização por papel e caso  
• transactional outbox, retries, idempotência e dead letter  
• frontend React/TypeScript com grafo, timeline, provenance e human-in-the-loop  
• containers non-root, filesystem read-only e smoke test do stack completo

A qualidade também faz parte do produto:

✅ 34 testes backend  
✅ 90,76% de cobertura branch-aware  
✅ 6 testes de frontend  
✅ 10/10 evals adversariais de grounding  
✅ 0 false accepts no conjunto versionado  
✅ migrations sem drift  
✅ PostgreSQL + OPA + API + web validados juntos na CI

Tudo no demo é sintético. Não estou apresentando o sistema como um produto AML certificado — estou mostrando como penso engenharia de IA para um domínio de alto risco: proveniência, governança, confiabilidade distribuída, segurança e responsabilidade humana desde o modelo de domínio.

Repositório: https://github.com/Runaway1457/evidencegraph-financial-crime

#AIEngineering #MachineLearning #KnowledgeGraph #FinancialCrime #AML #FastAPI #React #PostgreSQL #MLOps #SoftwareArchitecture

## LinkedIn — English launch post

**I did not want to build another portfolio chatbot.**

I wanted to answer a harder question: how should AI investigation software be designed when every material conclusion must be provable, reproducible, and independently reviewable?

That question became **EvidenceGraph Financial Crime** — an evidence-first investigation platform that turns synthetic financial records into an auditable relationship graph.

Its core principle is deliberately strict:

**the language model is not the source of truth.**

The trust path is:

Evidence → Graph Path → Hypothesis → Policy + Grounding → Independent Review → Finding

The repository demonstrates:

• a typed Python/FastAPI domain and control plane  
• PostgreSQL and drift-checked Alembic migrations  
• same-case relational integrity for edges and citations  
• SHA-256 evidence provenance, audit chain, and custody records  
• a deterministic investigator baseline  
• agent output treated as untrusted structured input  
• a fail-closed grounding gate for fabricated citations  
• OPA/Rego authorization scoped by role and case  
• transactional outbox, retry, idempotency, and dead-letter state  
• an advanced React/TypeScript graph investigation workspace  
• non-root read-only containers and a full-stack CI smoke test

Verified on the release branch:

✅ 34 backend tests, 90.76% branch-aware coverage  
✅ 6 frontend tests  
✅ 10/10 adversarial grounding evals, 0 false accepts  
✅ no Alembic schema drift  
✅ PostgreSQL + migration + OPA + API + web tested together

All data is synthetic. This is not presented as a certified AML product. It is a reviewable demonstration of how I approach AI engineering for high-risk domains: provenance, governance, distributed reliability, security, evaluation, and human accountability from the first domain invariant.

Repository: https://github.com/Runaway1457/evidencegraph-financial-crime

#AIEngineering #KnowledgeGraphs #FinancialCrime #AML #MLOps #ResponsibleAI #SoftwareArchitecture

## Short post

I built **EvidenceGraph Financial Crime** to explore a stricter AI architecture: the model may propose, but it cannot silently create truth.

Every finding must resolve to case-local evidence, survive a grounding gate, pass policy, and receive independent review.

The repository includes a graph investigation UI, typed FastAPI domain, PostgreSQL/Alembic, OPA, transactional outbox, deterministic baseline, adversarial evals, security docs, and a CI-smoked container stack.

34 backend tests · 90.76% branch coverage · 10/10 grounding evals · 0 false accepts.

https://github.com/Runaway1457/evidencegraph-financial-crime

## Carousel — 10-slide presentation

### Slide 1 — Cover

**EvidenceGraph Financial Crime**  
Evidence-first AI investigation  
Graph reasoning · Governed agents · Human accountability

Visual: full-width verified workbench screenshot.

### Slide 2 — The problem

**Financial investigations cannot trust fluent answers.**

A useful system must answer:

- Which source supports this claim?
- Did the source belong to this case?
- Can the reasoning path be reproduced?
- Who authorized the action?
- Who independently confirmed it?

### Slide 3 — The design principle

**The LLM is not the source of truth.**

Evidence → Graph → Hypothesis → Grounding → Policy → Review → Finding

Visual: the trust-chain diagram from the README.

### Slide 4 — Evidence-first domain

- Relationships require evidence.
- Findings require evidence.
- Composite foreign keys block cross-case references.
- Evidence content is addressed by SHA-256.
- Audit and custody events are hash-linked.

### Slide 5 — Governed AI

**Agent output is untrusted input.**

- structured proposals;
- atomic batch validation;
- no unknown or duplicate citations;
- bounded confidence;
- no direct confirmation;
- four-eyes review.

### Slide 6 — Reliable execution

**No fragile database → workflow dual write.**

- run + outbox committed atomically;
- leased dispatch;
- bounded exponential retry;
- idempotent workflow identity;
- dead-letter state;
- observable failure.

### Slide 7 — Investigation experience

Use a crop of the verified screenshot and call out:

1. risk-prioritized case queue;
2. multi-hop graph;
3. evidence inspector;
4. synchronized timeline;
5. non-authoritative copilot;
6. policy and provenance indicators.

### Slide 8 — Quality evidence

**Measured, not claimed.**

- 34 backend tests;
- 90.76% branch-aware coverage;
- 6 frontend tests;
- 10/10 adversarial grounding evals;
- 0 false accepts;
- schema drift check;
- full Compose smoke.

### Slide 9 — Production posture

- PostgreSQL 17;
- OPA/Rego;
- separate migration job;
- rootless multi-stage containers;
- read-only filesystems;
- isolated networks;
- health/readiness;
- threat model, ADRs, model card, data card, runbook.

Small footer: reference implementation; synthetic data; institution-specific validation required before regulated use.

### Slide 10 — Close

**I build AI systems where trust is an architecture property, not a prompt.**

GitHub: github.com/Runaway1457/evidencegraph-financial-crime  
Roles: Senior AI Engineer · AI Platform Engineer · Applied AI Engineer

## 90-second demo script

**0–15s — Context**  
“EvidenceGraph investigates synthetic financial-crime cases. The product starts from a strict rule: the model is never the source of truth.”

**15–35s — Graph**  
“Here the analyst explores a multi-hop transfer path. Selecting an edge updates the evidence inspector with confidence, source locator, digest, and provenance.”

**35–50s — Timeline**  
“The same case is synchronized against a material-event timeline so the analyst can test whether graph structure and temporal behavior tell the same story.”

**50–70s — Governed AI**  
“The copilot presents a hypothesis, not a verdict. It cites verified evidence, displays its reasoning path, and is visibly blocked from writing a confirmed finding.”

**70–82s — Engineering**  
“Underneath, PostgreSQL enforces same-case references, OPA governs actions, the grounding gate rejects fabricated citations, and the transactional outbox protects durable dispatch.”

**82–90s — Proof**  
“The repository includes the tests, eval dataset, policies, migrations, threat model, ADRs, runbook, containers, and CI evidence used to validate those claims.”

## Recruiter-facing talking points

- Why a relational system of record remains authoritative while a graph is treated as a projection.
- Why prompt instructions are not security controls.
- How batch validation prevents partial persistence of invalid agent output.
- How composite foreign keys defend invariants below the service layer.
- How a transactional outbox eliminates the commit/dispatch dual-write gap.
- Why a deterministic baseline is essential for regression and model-risk analysis.
- Which production obligations are intentionally left to the deploying institution.

## Asset checklist

- Primary image: `docs/assets/investigation-workbench.webp`
- Repository URL: `https://github.com/Runaway1457/evidencegraph-financial-crime`
- Recommended carousel ratio: 1080 × 1350
- Recommended demo video: 1920 × 1080, 60–90 seconds
- Use one metric per visual; keep disclaimers readable
- Never show real customer, banking, identity, or sanctions data
