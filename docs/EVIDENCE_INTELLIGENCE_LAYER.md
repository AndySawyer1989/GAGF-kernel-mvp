# Evidence Intelligence Layer

## Purpose

The Evidence Intelligence Layer is the Sprint 3.4 release layer for the GAGF/FIP Kernel MVP.

Its purpose is to evaluate incoming evidence before the deterministic kernel relies on it. It scores quality, checks cross-source agreement, detects conflicts, creates confidence scores, persists snapshot diagnostics, summarizes evidence health, and ranks risky snapshots.

This layer does not replace the GAGF Kernel. It improves the quality and explainability of the evidence supplied to the kernel.

## Release Marker

| Field | Value |
|---|---|
| Version | 0.5.0 |
| Release | evidence-intelligence |
| Sprint | 3.4 |
| Status | complete |

## Core Principle

No governance decision should be trusted more than the evidence supporting it.

The Evidence Intelligence Layer provides a deterministic way to answer:

- Is this evidence high quality?
- Which sources support it?
- Do sources agree?
- Are there conflicts?
- Which kernel evidence roles are missing?
- How confident should the snapshot be?
- Why did the snapshot get that confidence score?
- Which snapshots are risky?

## Architecture Flow

RawSecurityEvent list
→ EvidenceQualityService
→ CrossSourceAgreementService
→ EvidenceConflictService
→ EvidenceDiagnosticsService
→ EvidenceConfidenceAdapter
→ AdaptiveStateSnapshot.evidence_confidence
→ SnapshotDiagnosticsLedger
→ Summary and Risk Services

## Evidence Quality

Evidence quality is scored by EvidenceQualityService.

It evaluates timestamp quality, source registration, source enablement, metadata completeness, kernel role presence, and source trust tier.

Endpoint:

POST /evidence/quality

## Cross-Source Agreement

Cross-source agreement is scored by CrossSourceAgreementService.

It evaluates supporting sources, kernel role coverage, event type alignment, and source registration.

Endpoint:

POST /evidence/agreement

## Evidence Conflict Detection

Evidence conflicts are detected by EvidenceConflictService.

Current conflict families include security resolution mismatch, workflow state mismatch, and identity outcome mismatch.

Endpoint:

POST /evidence/conflicts

## Evidence Diagnostics

Evidence diagnostics are produced by EvidenceDiagnosticsService.

Diagnostics combine evidence quality, cross-source agreement, conflict health, and source coverage.

Endpoint:

POST /evidence/diagnostics

## Evidence Confidence

Evidence confidence is produced by EvidenceConfidenceAdapter.

The adapter converts diagnostics into the existing EvidenceConfidence schema.

Endpoint:

POST /evidence/confidence

## Snapshot Integration

The /snapshot endpoint now uses the Evidence Intelligence Layer.

Snapshot creation flow:

RawSecurityEvent list
→ MetricAdapter builds adaptive state
→ EvidenceConfidenceAdapter builds upgraded confidence
→ AdaptiveStateSnapshot is created
→ SnapshotLedger persists snapshot
→ SnapshotDiagnosticsLedger persists diagnostics

Endpoint:

POST /snapshot

## Ingestion Integration

The ingestion endpoints now save upgraded evidence confidence into ingestion-created snapshots.

Affected endpoints:

POST /ingest/github
POST /ingest/jira
POST /ingest/servicenow
POST /ingest/okta
POST /ingest/entra
POST /ingest/defender
POST /ingest/sentinelone

Ingestion responses now include evidence_confidence_score, evidence_confidence_band, and evidence_confidence_factors.

## Snapshot Diagnostics Persistence

Snapshot diagnostics are persisted by SnapshotDiagnosticsLedger.

Diagnostics are stored separately from snapshots and keyed by snapshot_id.

Endpoints:

GET /snapshot-diagnostics
GET /snapshot-diagnostics/{snapshot_id}

## Snapshot Diagnostics Summary

Snapshot diagnostics summaries are produced by SnapshotDiagnosticsSummaryService.

The summary includes record count, average confidence score, confidence band counts, diagnostic band counts, conflict summary, and source support summary.

Endpoint:

GET /snapshot-diagnostics/summary

## Snapshot Diagnostics Risk

Snapshot diagnostic risk is produced by SnapshotDiagnosticsRiskService.

The risk service ranks persisted snapshot diagnostics using low confidence, diagnostic degradation, conflict pressure, missing kernel roles, and low source support.

Endpoint:

GET /snapshot-diagnostics/risk

## Determinism Boundary

The Evidence Intelligence Layer is deterministic.

It does not use generative AI, subjective judgment, or probabilistic model output.

It provides scored evidence context to the kernel, but the deterministic GAGF Kernel remains authoritative.

## Kernel Boundary

The Evidence Intelligence Layer does not directly approve, reject, or override governance decisions.

It supports the kernel by improving evidence reliability, evidence explainability, confidence transparency, diagnostic traceability, and risk visibility.

The kernel still performs arbitration.

## Sprint 3.4 Story Map

| Story | Description |
|---|---|
| US-071 | Evidence Quality Score Service |
| US-072 | Evidence Quality Endpoint |
| US-073 | Cross-Source Agreement Service |
| US-074 | Cross-Source Agreement Endpoint |
| US-075 | Evidence Conflict Detection Service |
| US-076 | Evidence Conflict Endpoint |
| US-077 | Evidence Diagnostics Service |
| US-078 | Evidence Diagnostics Endpoint |
| US-079 | Evidence Confidence Adapter |
| US-080 | Evidence Confidence Endpoint |
| US-081 | Snapshot Evidence Confidence Integration |
| US-082 | Ingestion Evidence Confidence Integration |
| US-083 | Ingestion Confidence Response Transparency |
| US-084 | Snapshot Diagnostics Persistence |
| US-085 | Snapshot Diagnostics Summary Service |
| US-086 | Snapshot Diagnostics Summary Endpoint |
| US-087 | Snapshot Diagnostics Risk Service |
| US-088 | Snapshot Diagnostics Risk Endpoint |
| US-089 | Evidence Intelligence Hardening |
| US-090 | Sprint 3.4 Version / Release Marker |
| US-091 | Sprint 3.4 Documentation |

## Completed Capabilities

As of Sprint 3.4, the system can answer:

- Is this evidence reliable?
- How strong is the evidence quality?
- Do sources agree?
- Which sources support the evidence?
- Which kernel roles are missing?
- Are there source conflicts?
- What confidence should be assigned to this evidence?
- Why did a snapshot receive its confidence score?
- Which snapshots have evidence risk?

## Next Sprint Direction

The recommended next sprint is Sprint 3.5: Governance Signal + Correlation Layer.

Recommended flow:

Evidence Diagnostics
→ Governance Signal Classification
→ Correlation Detection
→ Friction Signal Detection
→ Governance Debt Indicators
→ Intervention Candidate Detection

This moves the system toward the Governance Alpha Engine chain:

Evidence
→ Friction Φ
→ Governance Debt
→ Adaptive Capacity A
→ Resilience R
→ Friction Dividend FD
→ Governance Alpha GA
→ Governance Learning
