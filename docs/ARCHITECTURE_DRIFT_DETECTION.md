# Architecture Drift Detection

## Purpose

Architecture Drift Detection is the diagnostic layer for comparing a baseline architecture diagnosis against a current architecture diagnosis.

It detects whether the platform or customer architecture is drifting toward:

- lower architectural diversity
- lower complexity resilience
- higher mononal risk
- worse platform architecture posture
- higher concentration risk

This extends Architectural Diversity Diagnostics from a static snapshot into a change-detection system.

## Diagnostic Flow

Baseline Architecture Diagnosis
→ Current Architecture Diagnosis
→ Score Drift
→ Posture Drift
→ Drift Status
→ Recommended Action
→ Dashboard Summary

The drift service does not create architecture changes. It only detects and explains structural regression or stability.

## Core Drift Metrics

### ADI Drift

ADI Drift measures the change in Architectural Diversity Index.

Formula:

architectural_diversity_index_delta =
current_architectural_diversity_index - baseline_architectural_diversity_index

Interpretation:

- positive ADI drift means diversity improved
- zero ADI drift means diversity is stable
- negative ADI drift means diversity regressed

### CRR Drift

CRR Drift measures the change in Complexity Resilience Ratio.

Formula:

complexity_resilience_ratio_delta =
current_complexity_resilience_ratio - baseline_complexity_resilience_ratio

Interpretation:

- positive CRR drift means resilience improved
- zero CRR drift means resilience is stable
- negative CRR drift means resilience regressed

### Mononal Risk Drift

Mononal Risk Drift measures whether concentration risk is increasing.

Formula:

mononal_risk_score_delta =
current_mononal_risk_score - baseline_mononal_risk_score

Interpretation:

- positive mononal risk drift means mononal risk increased
- zero mononal risk drift means mononal risk is stable
- negative mononal risk drift means mononal risk decreased

## Score Drift Fields

The drift service returns:

architectural_diversity_index_delta
complexity_resilience_ratio_delta
mononal_risk_score_delta
diversity_regressed
resilience_regressed
mononal_risk_increased
severity

## Drift Severity

The score drift severity may be:

none
low
moderate
high
critical

Current threshold logic:

critical:
ADI delta <= -0.25
or CRR delta <= -0.25
or mononal risk delta >= 0.25

high:
ADI delta <= -0.15
or CRR delta <= -0.15
or mononal risk delta >= 0.15

moderate:
ADI delta <= -0.05
or CRR delta <= -0.05
or mononal risk delta >= 0.05

low:
any smaller negative ADI drift
or any smaller negative CRR drift
or any smaller positive mononal risk drift

none:
no regression detected

## Posture Drift

Posture drift detects whether architecture classification changed between baseline and current states.

The posture drift result includes:

architecture_posture_changed
concentration_risk_changed
platform_architecture_status_changed
baseline_architecture_posture
current_architecture_posture
baseline_concentration_risk
current_concentration_risk
baseline_platform_architecture_status
current_platform_architecture_status
posture_regressed

## Platform Architecture Status Rank

Posture regression is evaluated by platform architecture status rank.

Current rank order:

platform_architecture_resilient
platform_architecture_balanced
platform_architecture_review
platform_architecture_concentrated
platform_architecture_mononal_risk
none

A move downward in this order is treated as posture regression.

## Drift Status

The service may return:

no_architecture_drift
low_architecture_drift
moderate_architecture_drift
high_architecture_drift
critical_architecture_drift

Interpretation:

no_architecture_drift means the current architecture remains stable against the baseline.

low_architecture_drift means minor regression exists and should be tracked.

moderate_architecture_drift means regression should be monitored.

high_architecture_drift means regression requires architectural review.

critical_architecture_drift means the architecture is drifting toward severe concentration or mononal risk and requires stabilization.

## Recommended Actions

The drift service may recommend:

continue_monitoring
track_architecture_drift
monitor_architecture_diversity_regression
review_architecture_regression_sources
stabilize_architecture_and_reduce_mononal_risk

## Services

### ArchitectureDriftDetectionService

File:

backend/app/gagf/architecture_drift_detection_service.py

Purpose:

baseline architecture diagnosis
+ current architecture diagnosis
→ score drift
→ posture drift
→ drift status
→ recommended action

### ArchitectureDriftDashboardService

File:

backend/app/gagf/architecture_drift_dashboard_service.py

Purpose:

architecture drift result
→ dashboard-ready scorecards
→ component_summary
→ posture_summary
→ risk_summary
→ operator_message
→ recommended_action

### ArchitecturalDiversityPlatformService

File:

backend/app/gagf/architectural_diversity_platform_service.py

Purpose:

current live platform architecture diagnosis
→ current_result for platform drift comparison

## Endpoints

### Manual Architecture Drift Endpoint

POST /governance/architecture/drift

Purpose:

Compares a provided baseline architecture diagnosis against a provided current architecture diagnosis.

### Platform Architecture Drift Endpoint

POST /governance/architecture/platform/drift

Purpose:

Compares a provided baseline architecture diagnosis against the current live platform architecture diagnosis.

This endpoint internally calls:

ArchitecturalDiversityPlatformService
ArchitectureDriftDetectionService

### Architecture Drift Dashboard Endpoint

POST /governance/architecture/drift/dashboard

Purpose:

Converts a raw architecture drift result into a dashboard-ready summary.

This endpoint internally calls:

ArchitectureDriftDashboardService

## Dashboard Output Contract

The drift dashboard summary returns:

status
summary_type
drift_status
drift_severity
operator_message
recommended_action
scorecards
component_summary
posture_summary
risk_summary

The scorecards include:

ADI Drift
CRR Drift
Mononal Risk Drift

## Operator Messages

Architecture drift dashboard messages include:

Architecture drift is critical and requires immediate stabilization.

Architecture drift is high and requires regression review.

Architecture drift is moderate and should be monitored.

Architecture drift is low and should be tracked.

No architecture drift is currently detected.

## Product Meaning

Architecture Drift Detection gives FIP/GAGF the ability to detect whether architecture is becoming more brittle over time.

It can support future product capabilities such as:

- architecture health monitoring
- resilience regression alerts
- mononal risk trend history
- governance topology review
- customer architecture assessment reports
- executive architecture risk summaries

## Relationship to Architectural Diversity Diagnostics

Architectural Diversity Diagnostics measures a single architecture state.

Architecture Drift Detection compares two architecture states.

Architectural Diversity Diagnostics answers:

What is the current architecture posture?

Architecture Drift Detection answers:

Has the architecture improved, stayed stable, or regressed?

## Test Contract Keywords

These exact terms are intentionally preserved for documentation contract tests.

ADI Drift
CRR Drift
Mononal Risk Drift

architectural_diversity_index_delta
complexity_resilience_ratio_delta
mononal_risk_score_delta

no_architecture_drift
low_architecture_drift
moderate_architecture_drift
high_architecture_drift
critical_architecture_drift

ArchitectureDriftDetectionService
ArchitectureDriftDashboardService
ArchitecturalDiversityPlatformService

POST /governance/architecture/drift
POST /governance/architecture/platform/drift
POST /governance/architecture/drift/dashboard

scorecards
component_summary
posture_summary
risk_summary
operator_message
recommended_action

## Constitutional Boundary

Architecture Drift Detection does not autonomously modify architecture.

It detects change, regression, stability, and risk.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain drift results later, but AI must not override ADI drift, CRR drift, mononal-risk drift, posture drift, or deterministic drift status calculations.
