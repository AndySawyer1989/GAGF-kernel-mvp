# Governance Diagnostic Chain

## Purpose

The Governance Diagnostic Chain is the Sprint 3.5 diagnostic layer for the GAGF/FIP Kernel MVP.

It converts normalized evidence events into deterministic governance diagnosis:

Raw Evidence
→ Governance Signal
→ Signal Summary
→ Signal Correlation
→ Friction Signal
→ Governance Debt Indicator
→ Intervention Candidate
→ Unified Diagnostic Chain

This layer does not replace the GAGF Kernel. It prepares structured, explainable diagnostic information for the deterministic governance layer.

## Constitutional Rule

The diagnostic chain must remain deterministic.

For the same input events, the system must produce the same governance signals, signal summary, signal correlations, friction signals, governance debt indicators, intervention candidates, and unified diagnostic chain posture.

No AI model is authoritative in this chain.

AI may explain, summarize, or explore possible interventions later, but the deterministic services remain the source of truth.

## Chain Stages

### 1. Governance Signal Classification

Service: GovernanceSignalService

Endpoint: POST /governance/signals

Purpose: Classifies each raw event into a governance signal type.

Current signal types:

- evidence_conflict
- security_risk
- identity_friction
- workflow_friction
- delivery_friction
- operational_incident
- governance_unknown

This stage answers: What does this evidence mean in governance terms?

### 2. Governance Signal Summary

Service: GovernanceSignalSummaryService

Endpoint: POST /governance/signals/summary

Purpose: Aggregates classified signals into a summary posture.

Important outputs:

- dominant_signal
- governance_posture
- average_signal_strength
- signal_counts
- source_distribution
- high_strength_signal_count

This stage answers: What is the dominant governance condition?

### 3. Signal Correlation

Service: SignalCorrelationService

Endpoint: POST /governance/signals/correlations

Purpose: Detects deterministic relationships between signals.

Current relationship examples:

- access_security_coupling
- process_delivery_coupling
- process_operations_coupling
- delivery_operations_coupling
- security_evidence_disagreement
- workflow_evidence_disagreement
- identity_evidence_disagreement
- same_signal_cluster

This stage answers: Which governance problems are reinforcing each other?

### 4. Friction Signal Detection

Service: FrictionSignalDetectionService

Endpoint: POST /governance/friction/signals

Purpose: Converts governance signals into friction signals.

Current friction types:

- evidence_friction
- security_pressure
- access_friction
- process_friction
- delivery_friction
- operational_friction

This stage answers: Where is governance drag forming?

### 5. Governance Debt Indicators

Service: GovernanceDebtIndicatorService

Endpoint: POST /governance/debt/indicators

Purpose: Converts friction signals into governance debt indicators.

Current debt types:

- evidence_debt
- security_governance_debt
- identity_governance_debt
- process_governance_debt
- delivery_governance_debt
- operational_governance_debt

Important outputs:

- governance_debt_score
- governance_debt_band
- debt_posture
- intervention_urgency
- amplifier_pressure

This stage answers: Is friction accumulating into governance liability?

### 6. Intervention Candidates

Service: InterventionCandidateService

Endpoint: POST /governance/interventions/candidates

Purpose: Converts governance debt indicators into recommended intervention candidates.

Current intervention types:

- evidence_reconciliation
- security_policy_review
- access_policy_tuning
- process_refactor
- delivery_pipeline_review
- operations_stabilization

Important outputs:

- dominant_intervention_type
- intervention_posture
- recommended_next_action
- priority_score
- priority_band

This stage answers: What should governance review first?

### 7. Unified Diagnostic Chain

Service: GovernanceDiagnosticChainService

Endpoint: POST /governance/diagnostics/chain

Purpose: Bundles the full diagnostic chain into one deterministic response.

The unified chain includes:

- signal_summary
- correlation_result
- friction_result
- debt_result
- intervention_result
- chain_summary

This stage answers: What is the full governance diagnosis?

## Chain Summary Contract

The unified diagnostic chain must return a chain_summary containing:

- dominant_signal
- governance_posture
- correlation_posture
- dominant_friction_type
- friction_posture
- dominant_debt_type
- governance_debt_score
- governance_debt_band
- debt_posture
- intervention_urgency
- dominant_intervention_type
- intervention_posture
- signal_count
- correlation_count
- friction_signal_count
- debt_indicator_count
- intervention_candidate_count

## Chain Postures

The unified chain may return:

- none
- low_governance_diagnosis
- moderate_governance_diagnosis
- high_governance_diagnosis
- critical_governance_diagnosis

Interpretation:

none means no events were provided.

low_governance_diagnosis means evidence was classified, but no friction, debt, or intervention chain formed.

moderate_governance_diagnosis means friction, debt, or intervention signals exist but have not crossed high thresholds.

high_governance_diagnosis means the chain shows high friction, high debt, or prioritized intervention.

critical_governance_diagnosis means the chain shows critical debt, a critical debt band, or immediate intervention.

## Example Diagnostic Paths

### Security Risk Path

Defender event
→ security_risk
→ urgent_attention
→ security_pressure
→ security_governance_debt
→ security_policy_review
→ critical_governance_diagnosis

### Identity + Security Coupling Path

Okta failed login + Defender active security event
→ identity_friction + security_risk
→ access_security_coupling
→ access_friction + security_pressure
→ identity_governance_debt + security_governance_debt
→ access_policy_tuning + security_policy_review
→ critical_governance_diagnosis

### Process + Delivery Path

Jira approval delay + GitHub review requirement
→ workflow_friction + delivery_friction
→ process_delivery_coupling
→ process_friction + delivery_friction
→ process_governance_debt + delivery_governance_debt
→ process_refactor + delivery_pipeline_review
→ high_governance_diagnosis

### Evidence Conflict Path

Security resolution mismatch
→ evidence_conflict
→ reconcile_evidence
→ evidence_friction
→ evidence_debt
→ evidence_reconciliation
→ critical_governance_diagnosis

### Unknown Classification Path

Unknown source event
→ governance_unknown
→ classification_gap
→ no friction signal
→ no debt indicator
→ no intervention candidate
→ low_governance_diagnosis

## Sprint 3.5 Endpoint Surface

Sprint 3.5 owns the following governance diagnostic endpoints:

- POST /governance/signals
- POST /governance/signals/summary
- POST /governance/signals/correlations
- POST /governance/friction/signals
- POST /governance/debt/indicators
- POST /governance/interventions/candidates
- POST /governance/diagnostics/chain

## Sprint 3.5 Test Protection

The diagnostic chain is protected by service tests, endpoint tests, and hardening tests.

Hardening tests verify that:

- all Sprint 3.5 routes exist
- empty payloads remain deterministic
- individual endpoint outputs match the unified diagnostic chain
- security diagnosis remains stable
- evidence conflict diagnosis remains stable
- unknown classification gap remains stable

## Product Meaning

Sprint 3.5 creates the first working version of the FIP/GAGF governance diagnosis pipeline.

The platform can now move from:

What happened?

to:

What does it mean?
Where is friction forming?
Is it becoming governance debt?
What intervention should be considered first?

This is the foundation for later stages:

- Adaptive Capacity
- Resilience
- Friction Dividend
- Governance Alpha
- Governance Learning

## Architectural Boundary

The diagnostic chain is advisory to the GAGF Kernel.

It can recommend and prioritize intervention candidates, but it does not autonomously execute governance changes.

The deterministic Kernel remains the authoritative decision and verification layer.
