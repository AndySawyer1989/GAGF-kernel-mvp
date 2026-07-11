# ZTA Control Mapping

## Purpose

ZTA Control Mapping defines Zero Trust Architecture requirements for FIP/GAGF products based on their product security tier.

Not every product requires full Zero Trust Architecture.

Tier 1 and Tier 2 products may use standard or enterprise security controls.

Tier 3 Regulated / Sensitive products require regulated Zero Trust planning.

Tier 4 Federal / Critical Infrastructure products require federal-grade Zero Trust Architecture planning.

## Mapping Flow

Product Security Tier
→ ZTA Requirement Level
→ Identity Controls
→ Access Enforcement Controls
→ Session and Device Controls
→ Segmentation Controls
→ Telemetry and Evidence Requirements
→ Deployment Implications
→ Recommended Next Action

## Security Tier Relationship

### Tier 1 — Standard Commercial

Internal value:

tier_1_standard_commercial

ZTA requirement level:

not_required

Purpose:

Tier 1 products use a standard commercial security baseline.

Typical examples:

- Assessment Factory Lite
- public demos
- low-risk product experiments
- low-risk analytics tools

Recommended action:

apply_standard_security_baseline

### Tier 2 — Enterprise Secure

Internal value:

tier_2_enterprise_secure

ZTA requirement level:

recommended

Purpose:

Tier 2 products should evaluate Zero Trust readiness for enterprise use, but ZTA is not automatically required.

Typical examples:

- FIP Governance Diagnostics SaaS
- Embedded FIP Enterprise API
- enterprise customer dashboards
- customer governance diagnostics

Recommended action:

evaluate_zero_trust_readiness_for_enterprise_use

### Tier 3 — Regulated / Sensitive

Internal value:

tier_3_regulated_sensitive

ZTA requirement level:

required_regulated

Purpose:

Tier 3 products require regulated Zero Trust planning because they may handle health data, regulated data, sensitive customer data, or sensitive security telemetry.

Typical examples:

- FIP Healthcare Readiness Diagnostic
- regulated compliance readiness assessments
- sensitive security telemetry diagnostics
- regulated customer telemetry analysis

Recommended action:

implement_regulated_zero_trust_control_plan

### Tier 4 — Federal / Critical Infrastructure

Internal value:

tier_4_federal_critical

ZTA requirement level:

required_federal_high

Purpose:

Tier 4 products require federal-grade Zero Trust Architecture planning because they may target federal, air-gapped, on-prem, FedRAMP High-aligned, or critical infrastructure environments.

Typical examples:

- FIP Secure
- ESY secure runtime
- federal governance diagnostics
- air-gapped security diagnostics
- critical infrastructure governance tooling

Recommended action:

implement_federal_zero_trust_architecture_plan

## ZTA Requirement Levels

The service may return:

not_required
recommended
required_regulated
required_federal_high

Interpretation:

not_required means standard security controls are enough for the current product tier.

recommended means Zero Trust readiness should be evaluated for enterprise use.

required_regulated means Zero Trust controls are required for regulated or sensitive product use.

required_federal_high means federal-grade Zero Trust Architecture controls are required.

## Tier 3 Regulated ZTA Controls

Tier 3 identity controls include:

strong_identity_boundary
mfa_or_passkeys
least_privilege_access
role_based_access_control
access_lifecycle_management
identity_access_chain_evidence

Tier 3 access enforcement controls include:

policy_based_access_control
least_privilege_access
continuous_session_verification
tenant_isolation_enforcement
minimum_necessary_access
sensitive_action_approval

Tier 3 session and device controls include:

device_trust_evaluation
continuous_session_verification
session_timeout
risk_based_reauthentication

Tier 3 segmentation controls include:

tenant_boundary_segmentation
regulated_data_boundary
environment_boundary_enforcement

Tier 3 telemetry and evidence requirements include:

audit_evidence_for_access_decisions
identity_access_chain_evidence
session_verification_evidence
regulated_data_access_evidence
minimum_necessary_access_evidence
zta_control_mapping_record

Tier 3 deployment implications include:

private_tenant_saas_preferred
customer_controlled_environment_supported
regulated_data_boundary_required
enhanced_audit_boundary_required

## Tier 4 Federal ZTA Controls

Tier 4 identity controls include:

hardware_backed_identity
mfa_or_passkeys
privileged_access_step_up
strong_service_identity
short_lived_signed_tokens
identity_access_chain_evidence

Tier 4 access enforcement controls include:

policy_decision_point
policy_enforcement_point
default_deny_access
continuous_policy_evaluation
mutual_tls
privileged_action_approval
tenant_isolation_enforcement

Tier 4 session and device controls include:

device_posture_validation
continuous_verification
session_risk_scoring
short_session_lifetime
managed_device_requirement
privileged_session_recording

Tier 4 segmentation controls include:

microsegmentation
network_policy_enforcement
workload_identity_segmentation
tenant_boundary_segmentation
environment_boundary_enforcement

Tier 4 telemetry and evidence requirements include:

immutable_access_evidence
policy_decision_evidence
policy_enforcement_evidence
device_posture_evidence
privileged_access_evidence
mutual_tls_session_evidence
continuous_monitoring_record
zta_control_mapping_record

Tier 4 deployment implications include:

private_cloud_or_on_prem_preferred
air_gapped_supported_when_required
government_authorized_cloud_supported
strict_control_boundary_required
continuous_monitoring_required

## Service

### ZTAControlMappingService

File:

backend/app/gagf/zta_control_mapping_service.py

Purpose:

product security result
→ ZTA requirement level
→ identity controls
→ access enforcement controls
→ session/device controls
→ segmentation controls
→ telemetry/evidence requirements
→ deployment implications
→ recommended next action

## Endpoint

### ZTA Control Mapping Endpoint

POST /products/zta-controls

Purpose:

Maps a product security tier result to Zero Trust Architecture controls.

Example input:

{
  "product_name": "fip_secure",
  "security_tier": "tier_4_federal_critical"
}

Example output includes:

status
mapping_type
product_name
security_tier
zta_required
zta_requirement_level
identity_controls
access_enforcement_controls
session_and_device_controls
segmentation_controls
telemetry_and_evidence_requirements
deployment_implications
recommended_next_action

## Relationship to Product Security Tiering

Product Security Tiering determines the security tier.

ZTA Control Mapping determines whether Zero Trust is required and what controls are needed.

Product Security Tiering answers:

What security tier is this product?

ZTA Control Mapping answers:

What Zero Trust controls are required for this tier?

## Product Strategy Meaning

ZTA Control Mapping allows FIP/GAGF to avoid overburdening low-risk products while still requiring strong controls for regulated and federal products.

This supports a tiered product strategy:

Tier 1:
Move fast with standard commercial controls.

Tier 2:
Prepare for enterprise security and SOC 2 readiness.

Tier 3:
Implement regulated Zero Trust planning for HIPAA-sensitive and sensitive-data products.

Tier 4:
Implement federal-grade Zero Trust Architecture for FedRAMP High-aligned, air-gapped, on-prem, or critical infrastructure products.

## Product Examples

Assessment Factory Lite:

tier_1_standard_commercial
not_required

FIP Governance Diagnostics SaaS:

tier_2_enterprise_secure
recommended

FIP Healthcare Readiness Diagnostic:

tier_3_regulated_sensitive
required_regulated

FIP Secure:

tier_4_federal_critical
required_federal_high

ESY secure runtime:

tier_4_federal_critical
required_federal_high

## Compliance Boundary

ZTA Control Mapping does not certify a product as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It identifies Zero Trust control requirements and evidence requirements.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

ZTA Control Mapping does not autonomously grant, deny, or modify access.

It maps product tiers to required controls.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain ZTA control recommendations later, but AI must not override deterministic ZTA control mapping without human-approved policy changes.
