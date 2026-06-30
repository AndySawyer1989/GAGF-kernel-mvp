\# Architecture Decision Records



\## ADR-001 — Deterministic Kernel First



Decision:



The GAGF Kernel remains deterministic and policy-governed.



Reason:



Governance decisions must be auditable, replayable, and explainable.



Implication:



The Kernel uses explicit GPL rules rather than opaque AI decision-making.



\---



\## ADR-002 — AI Advisory Layer



Decision:



AI will be added later as an advisory layer, not as the authority.



AI may:



\- Explain decisions

\- Generate reports

\- Query governance history

\- Suggest hypotheses

\- Assist operators



AI may not directly modify:



\- GPL policy

\- Kernel arbitration logic

\- Evidence records

\- Snapshot Ledger

\- Decision Ledger



Reason:



The system must preserve evidence integrity and deterministic governance.



Preferred architecture:



```text

Evidence

&#x20;  ↓

MetricAdapter

&#x20;  ↓

Adaptive Snapshot

&#x20;  ↓

GPL Policy

&#x20;  ↓

Kernel Arbitration

&#x20;  ↓

Decision Ledger

&#x20;  ↓

AI Advisory Layer

&#x20;  ↓

Human Review

