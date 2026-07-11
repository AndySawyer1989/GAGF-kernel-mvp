# Architectural Diversity Diagnostics

## Purpose

Architectural Diversity Diagnostics is the altered-roadmap diagnostic layer for detecting architecture concentration, mononal risk, and resilience potential inside the GAGF/FIP platform.

It converts architecture component records into deterministic measurements:

Architecture Components
→ Component Type Diversity
→ Subsystem Diversity
→ Authority Zone Diversity
→ Redundancy Diversity
→ Architectural Diversity Index
→ Complexity Resilience Ratio
→ Mononal Risk Score
→ Architecture Posture

This layer answers:

Is the architecture diverse enough to resist brittle concentration?
Is too much authority, responsibility, or function concentrated in one pattern?
Is the platform trending toward adaptive architecture or mononal risk?

## Core Metrics

### ADI — Architectural Diversity Index

ADI measures how diverse the architecture is across four dimensions:

- component_type_diversity
- subsystem_diversity
- authority_zone_diversity
- redundancy_diversity

Current formula:

ADI =
(
  component_type_diversity
  + subsystem_diversity
  + authority_zone_diversity
  + redundancy_diversity
) / 4

Each diversity dimension is currently calculated as:

unique_values / component_count

Higher ADI means more architectural diversity.
Lower ADI means more concentration and mononal risk.

### CRR — Complexity Resilience Ratio

CRR measures whether architectural diversity, redundancy, and interface balance create resilience instead of uncontrolled complexity.

Current formula:

CRR =
ADI * 0.60
+ redundancy_diversity * 0.25
+ interface_balance_score * 0.15

Higher CRR means complexity is more resilient and distributed.
Lower CRR means complexity is more concentrated, brittle, or under-diversified.

### Mononal Risk Score

Mononal risk estimates how strongly the architecture is collapsing into one dominant pattern.

Current formula:

mononal_risk_score = 1.0 - ADI

Higher mononal risk means greater concentration risk.
Lower mononal risk means greater architectural diversity.

## Component Contract

Architectural Diversity Diagnostics expects component records with the following fields:

- component_id
- component_type
- subsystem
- authority_zone
- redundancy_group
- dependencies
- interfaces
- criticality

Example:

{
  "component_id": "gagf-kernel",
  "component_type": "kernel",
  "subsystem": "decision",
  "authority_zone": "kernel",
  "redundancy_group": "kernel-core",
  "dependencies": ["snapshot-ledger", "decision-ledger"],
  "interfaces": ["arbitration", "policy", "decision"],
  "criticality": "critical"
}

## Supported Alias Fields

The diagnostic service normalizes several aliases.

Component identity:

- component_id
- id
- name

Component type:

- component_type
- type

Subsystem:

- subsystem
- domain

Authority zone:

- authority_zone
- decision_authority
- owner_zone

Redundancy group:

- redundancy_group
- partition
- component_id fallback

This allows manual architecture inputs and platform-generated telemetry to share the same diagnostic path.

## Architecture Postures

The diagnostic service may return:

- none
- adaptive_diverse_architecture
- mixed_resilience_architecture
- concentrated_architecture
- mononal_architecture_risk

Interpretation:

none means no components were provided.

adaptive_diverse_architecture means ADI and CRR are both strong. Architecture appears distributed, diverse, and resilient.

mixed_resilience_architecture means architecture has meaningful diversity but also visible concentration pressure.

concentrated_architecture means architecture has enough concentration to require review.

mononal_architecture_risk means architecture is collapsing toward a single dominant pattern or authority concentration.

## Concentration Risk Bands

The diagnostic service may return:

- none
- low
- moderate
- high
- critical

Current logic:

0.00 means none
less than 0.25 means low
greater than or equal to 0.25 means moderate
greater than or equal to 0.50 means high
greater than or equal to 0.75 means critical

## Platform Architecture Status

The platform diagnostic service converts architecture posture and concentration risk into a platform-level status:

- platform_architecture_resilient
- platform_architecture_balanced
- platform_architecture_concentrated
- platform_architecture_mononal_risk
- platform_architecture_review
- none

Priority rule:

mononal risk overrides ordinary concentration.
critical concentration overrides lower status.
adaptive diverse plus low or none risk means resilient.
mixed resilience plus low or moderate risk means balanced.
concentrated or high risk means concentrated.

## Services

### ArchitecturalDiversityDiagnosticService

File:

backend/app/gagf/architectural_diversity_diagnostic_service.py

Purpose:

Manual component records
→ ADI
→ CRR
→ mononal risk
→ architecture posture
→ component diagnostics

### ArchitecturalDiversityTelemetryAdapter

File:

backend/app/gagf/architectural_diversity_telemetry_adapter.py

Purpose:

SourceRegistry
→ source connector components
→ kernel platform components
→ ADI/CRR-ready component records

Platform kernel components currently include:

- gagf-kernel
- snapshot-ledger
- decision-ledger
- governance-diagnostic-chain

Source systems currently mapped include:

- github
- jira
- servicenow
- okta
- entra
- defender
- sentinelone

### ArchitecturalDiversityPlatformService

File:

backend/app/gagf/architectural_diversity_platform_service.py

Purpose:

ArchitecturalDiversityTelemetryAdapter
→ ArchitecturalDiversityDiagnosticService
→ platform architecture diagnosis

This service produces platform-level ADI, CRR, mononal risk, component counts, diversity breakdowns, and component diagnostics.

## Endpoints

### Manual Architecture Diagnostic Endpoint

POST /governance/architecture/diversity

Purpose:

Accepts a list of architecture component records and returns ADI / CRR diagnostics.

Input example:

[
  {
    "component_id": "api-1",
    "component_type": "api",
    "subsystem": "interface",
    "authority_zone": "edge",
    "redundancy_group": "api-a",
    "dependencies": ["kernel-1"],
    "interfaces": ["http", "webhook"],
    "criticality": "high"
  }
]

### Platform Architecture Diagnostic Endpoint

GET /governance/architecture/platform

Purpose:

Builds architecture components from platform telemetry and returns ADI / CRR diagnostics.

This endpoint uses:

SourceRegistry
+ kernel platform components
+ ArchitecturalDiversityTelemetryAdapter
+ ArchitecturalDiversityDiagnosticService

## Integration Contract

The platform endpoint must remain round-trip compatible with the manual endpoint.

The following flow must produce matching diagnostic scores and postures:

GET /governance/architecture/platform
→ extract components
→ POST /governance/architecture/diversity
→ compare ADI, CRR, mononal risk, postures, counts, and breakdowns

This guarantees that platform-generated architecture telemetry and manual component input use the same deterministic diagnostic logic.

## Product Meaning

Architectural Diversity Diagnostics gives FIP/GAGF an architecture-level view of governance resilience.

It can identify whether the platform or a customer system is:

- diverse and adaptive
- balanced but concentrated
- over-concentrated
- mononal and brittle

This supports the larger Governance Alpha Engine by preparing later stages:

- Adaptive Capacity
- Resilience
- Friction Dividend
- Governance Alpha
- Governance Learning

## Constitutional Boundary

Architectural Diversity Diagnostics does not autonomously change architecture.

It diagnoses structure, concentration, and resilience potential.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain the diagnostic result later, but AI must not override ADI, CRR, or mononal-risk calculations.
