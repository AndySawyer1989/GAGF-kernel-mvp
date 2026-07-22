# Evidence Confidence Contracts

## Purpose

This document defines the current evidence-confidence calculation surfaces in the GAGF Kernel MVP.

The repository currently contains two separate evidence-confidence calculations. They serve different paths, use different precision contracts, and must not be silently substituted for one another.

This inventory establishes compatibility rules before future consolidation, migration, or replacement work.

---

## Contract 1: Diagnostics-Based Evidence Confidence

### Implementation

- Module: `backend.app.gagf.evidence_confidence_adapter`
- Class: `EvidenceConfidenceAdapter`
- Entry point: `EvidenceConfidenceAdapter.build_confidence(events)`
- Calculation method: `EvidenceConfidenceAdapter.calculate_confidence_score(diagnostics)`

### Identity

- Calculation ID: `evidence-confidence`
- Version: `0.1.0-diagnostics`
- Status: `PROVISIONAL_HEURISTIC`
- Authority: `NON_AUTHORITATIVE`

### Inputs

The adapter accepts a list of evidence events and delegates evidence analysis to:

- `EvidenceDiagnosticsService`
- Evidence quality scoring
- Cross-source agreement analysis
- Evidence conflict analysis
- Source coverage analysis

### Calculation factors

The confidence score currently combines:

- Evidence quality: 35 percent
- Cross-source agreement: 30 percent
- Conflict health: 20 percent
- Source coverage: 15 percent

### Precision

The diagnostics-based confidence score is rounded to four decimal places.

Examples currently protected by tests include:

- `0.9622`
- `0.874`
- `0.8074`
- `0.586`
- `0.35`

### Top-level output contract

`build_confidence()` returns a dictionary containing the following established keys:

- `status`
- `event_count`
- `source_count`
- `diagnostic_score`
- `diagnostic_band`
- `confidence_score`
- `confidence_band`
- `supporting_sources`
- `kernel_roles_present`
- `missing_roles`
- `evidence_confidence`
- `diagnostics`
- `calculation_metadata`

Future fields may be added, but existing keys must not be removed, renamed, or silently changed without an explicit version migration.

### EvidenceConfidence factor contract

The nested `evidence_confidence.factors` mapping currently contains:

- `evidence_quality`
- `cross_source_agreement`
- `conflict_health`
- `source_coverage`
- `diagnostic_score`

These factor names are compatibility-sensitive because adapter and endpoint tests depend on them.

### Current consumers

Known consumers include:

- Evidence-confidence API endpoint
- Main FastAPI orchestration
- Snapshot construction paths
- Snapshot diagnostics persistence
- Snapshot diagnostics summary services
- Snapshot diagnostics risk services
- Adapter tests
- Endpoint tests
- Confidence version-contract tests

### Role

This is the current diagnostics-based candidate for future canonical confidence calculation.

It is not yet authoritative and must not independently authorize governance decisions.

---

## Contract 2: Legacy MetricAdapter Confidence

### Implementation

- Module: `backend.app.gagf.metric_adapter`
- Class: `MetricAdapter`
- Internal entry point: `MetricAdapter._calculate_evidence_confidence(events)`

### Identity

- Calculation ID: `metric-adapter-evidence-confidence`
- Version: `0.1.0-legacy`
- Status: `LEGACY_HEURISTIC`
- Authority: `NON_AUTHORITATIVE`

### Inputs

The legacy calculator receives the subset of `RawSecurityEvent` records where:

- `kernel_eligible` is true

### Calculation factors

The legacy confidence score currently combines:

- Timestamp quality: 40 percent
- Sensor reliability: 25 percent
- Cross-source agreement: 20 percent
- Telemetry completeness: 15 percent

Sensor reliability is currently fixed at:

- `0.90`

Cross-source agreement is currently assigned as:

- `1.0` when more than one source system is present
- `0.7` when one or zero source systems are present for a non-empty batch

### Precision

The legacy confidence score is rounded to three decimal places.

Factor precision is also rounded to three decimal places where applicable.

### Output contract

The calculator returns an `EvidenceConfidence` model containing:

- `score`
- `factors`

The factor mapping contains:

- `timestamp_quality`
- `sensor_reliability`
- `cross_source_agreement`
- `telemetry_completeness`

For an empty eligible event batch, the score and all factors are `0.0`.

### Current consumers

Known consumers include:

- `MetricAdapter.build_snapshot()`
- Snapshot creation
- Ingestion service paths
- Snapshot ledger persistence
- Dashboard and presentation paths
- MetricAdapter-related tests
- Normalization rule-set tests
- Legacy confidence version-contract tests

### Role

This is a legacy local calculator preserved for compatibility.

It is not the canonical diagnostics-based confidence implementation and must not be expanded into a new authoritative path.

---

## Calculator Differences

| Property | Diagnostics-Based Adapter | Legacy MetricAdapter |
|---|---|---|
| Calculation ID | `evidence-confidence` | `metric-adapter-evidence-confidence` |
| Version | `0.1.0-diagnostics` | `0.1.0-legacy` |
| Status | `PROVISIONAL_HEURISTIC` | `LEGACY_HEURISTIC` |
| Authority | `NON_AUTHORITATIVE` | `NON_AUTHORITATIVE` |
| Precision | Four decimal places | Three decimal places |
| Evidence quality | Included | Not included directly |
| Conflict health | Included | Not included |
| Source coverage | Included | Not included |
| Timestamp quality | Indirect through diagnostics | Direct factor |
| Sensor reliability | Not fixed locally | Fixed at `0.90` |
| Return type | Dictionary with nested model | `EvidenceConfidence` model |
| Primary role | Canonical candidate | Legacy compatibility path |

---

## Compatibility Rules

### Additive response evolution

Existing response keys and nested factor names must remain stable.

New metadata or diagnostic fields may be added only when they are additive and do not change established values.

### No silent calculator substitution

No caller may switch from one calculator to the other without:

1. An explicit migration story.
2. A new calculation version.
3. Caller inventory updates.
4. Regression tests for every affected consumer.
5. Replay or deterministic comparison tests.
6. Documentation of expected score changes.
7. Approval of compatibility impact.

### No silent precision changes

Changing score precision from three to four decimals, or four to three decimals, is a contract change.

Such a change requires a new calculation version and migration tests.

### No silent factor changes

Adding a factor may be additive only when it does not alter existing scores.

Removing, renaming, reweighting, or changing the interpretation of a factor requires a new calculation version.

### No authority escalation

Neither calculator may become authoritative merely through reuse by a governance endpoint or service.

Authority must be granted explicitly through a constitutional contract and corresponding tests.

### Replay requirement

Future confidence consolidation must prove deterministic replay for identical:

- Canonical evidence
- Evidence ordering
- Source registry version
- Calculation version
- Weight configuration
- Policy state

### Migration requirement

A future canonical confidence implementation must provide:

- Old calculation identity
- New calculation identity
- Old and new version numbers
- Before-and-after score comparison
- Affected caller list
- Compatibility strategy
- Rollback path
- Replay evidence
- Updated contract documentation

---

## Current Consolidation Position

The diagnostics-based adapter is the preferred candidate for future canonicalization because it incorporates broader evidence diagnostics.

The legacy MetricAdapter calculation remains operational for compatibility and snapshot continuity.

No consolidation is authorized by this document.

This document only establishes the current contracts and the rules required for safe future migration.
