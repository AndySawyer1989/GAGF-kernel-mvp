# Product Security Tiering

## Purpose

Product Security Tiering classifies each FIP/GAGF product by its security, compliance, deployment, and evidence requirements.

Not every product needs FedRAMP High, HIPAA, or SOC 2-level protection.

Some products can operate as standard commercial tools, while others require enterprise, regulated, federal, air-gapped, or critical-infrastructure security controls.

This service prevents overengineering low-risk products while making sure high-risk products receive the correct security posture.

## Classification Flow

Product Profile
→ Product Security Tier
→ Compliance Alignment
→ Required Controls
→ Deployment Models
→ Evidence Requirements
→ Recommended Next Action

## Security Tiers

### Tier 1 — Standard Commercial

Internal value:

tier_1_standard_commercial

Label:

Standard Commercial

Purpose:

For public demos, low-risk tools, early commercial pilots, and products that do not handle sensitive customer data.

Example products:

- Assessment Factory Lite
- public demo tools
- low-risk analytics demos
- early product experiments

Typical compliance alignment:

- secure_coding_baseline
- basic_privacy_practices

Typical deployment models:

- public_saas
- demo_environment

### Tier 2 — Enterprise Secure

Internal value:

tier_2_enterprise_secure

Label:

Enterprise Secure

Purpose:

For enterprise SaaS, governance diagnostics, customer telemetry, and products that require strong tenant isolation, auditability, and SOC 2 readiness.

Example products:

- FIP Governance Diagnostics SaaS
- FIP Assessment Factory Enterprise
- Embedded FIP Enterprise API
- customer governance dashboards

Typical compliance alignment:

- soc_2_readiness
- enterprise_security_baseline
- tenant_isolation

Typical deployment models:

- enterprise_saas
- private_tenant_saas
- managed_private_cloud

### Tier 3 — Regulated / Sensitive

Internal value:

tier_3_regulated_sensitive

Label:

Regulated / Sensitive

Purpose:

For products that handle healthcare data, sensitive data, regulated data, or high-risk security telemetry.

Example products:

- FIP Healthcare Readiness Diagnostic
- security telemetry diagnostic modules
- sensitive compliance readiness assessments
- regulated customer telemetry analysis

Typical compliance alignment:

- soc_2_readiness
- hipaa_security_rule_alignment
- enhanced_auditability
- data_protection_controls

Typical deployment models:

- private_tenant_saas
- managed_private_cloud
- customer_controlled_environment

### Tier 4 — Federal / Critical Infrastructure

Internal value:

tier_4_federal_critical

Label:

Federal / Critical Infrastructure

Purpose:

For federal, air-gapped, on-prem, critical infrastructure, or FedRAMP High-aligned deployments.

Example products:

- FIP Secure
- ESY secure runtime
- federal governance diagnostics
- critical infrastructure governance tooling
- air-gapped security diagnostics

Typical compliance alignment:

- fedramp_high_alignment
- nist_800_53_alignment
- soc_2_readiness
- continuous_monitoring
- air_gapped_or_private_deployment_readiness

Typical deployment models:

- private_cloud
- on_prem
- air_gapped
- government_authorized_cloud

## Tier Decision Rules

Tier 4 overrides lower tiers when a product:

- targets federal customers
- requires air gap
- requires on-prem deployment

Tier 3 applies when a product:

- targets healthcare
- handles health data
- handles security telemetry and sensitive data together

Tier 2 applies when a product:

- targets enterprise customers
- handles customer data
- handles sensitive data
- handles security telemetry

Tier 1 applies when a product does not require elevated compliance controls.

## Product Profile Fields

The service accepts product profile fields such as:

product_name
product_category
handles_customer_data
handles_sensitive_data
handles_security_telemetry
handles_health_data
targets_enterprise
targets_healthcare
targets_federal
requires_air_gap
requires_on_prem
is_public_demo
is_internal_only

## Required Controls

The ProductSecurityTierService maps each tier to required controls.

Tier 1 controls include:

- authentication
- basic_authorization
- secure_logging
- backup_and_recovery
- secure_development_practices

Tier 2 controls include:

- role_based_access_control
- tenant_isolation
- encryption_in_transit
- encryption_at_rest
- audit_logging
- change_management
- incident_response
- access_lifecycle_management

Tier 3 controls include:

- role_based_access_control
- tenant_isolation
- encryption_in_transit
- encryption_at_rest
- immutable_audit_logging
- minimum_necessary_access
- risk_analysis
- risk_management
- incident_response
- data_retention_and_disposal
- enhanced_access_review

Tier 4 controls include:

- hardware_backed_authentication
- mfa_or_passkeys
- mutual_tls
- default_deny_access
- immutable_evidence_ledgers
- strict_tenant_isolation
- continuous_monitoring
- vulnerability_management
- configuration_baselines
- incident_response
- poam_tracking
- supply_chain_risk_management
- secure_boot_or_chain_of_trust

## Evidence Requirements

Each tier has evidence requirements.

Tier 1 evidence includes:

- release_marker
- test_results
- basic_security_log

Tier 2 evidence includes:

- release_marker
- test_results
- access_review_evidence
- audit_log_export
- change_management_record
- incident_response_record

Tier 3 evidence includes:

- release_marker
- test_results
- access_review_evidence
- immutable_audit_log_export
- risk_analysis_record
- risk_management_record
- data_retention_record
- incident_response_record
- privacy_boundary_record

Tier 4 evidence includes:

- release_marker
- test_results
- control_mapping_record
- continuous_monitoring_record
- configuration_baseline_record
- vulnerability_scan_record
- poam_record
- chain_of_trust_record
- immutable_evidence_ledger_export
- incident_response_record
- authorization_boundary_record

## Service

### ProductSecurityTierService

File:

backend/app/gagf/product_security_tier_service.py

Purpose:

product profile
→ security tier
→ compliance alignment
→ required controls
→ deployment model
→ evidence requirements
→ recommended next action

## Endpoint

### Product Security Tier Endpoint

POST /products/security-tier

Purpose:

Classifies a product profile into a security tier.

Example input:

{
  "product_name": "FIP Governance Diagnostics SaaS",
  "product_category": "governance_diagnostics",
  "targets_enterprise": true,
  "handles_customer_data": true
}

Example output includes:

status
classification_type
product_name
product_category
security_tier
security_tier_label
compliance_alignment
required_controls
deployment_models
evidence_requirements
recommended_next_action
classification_reason
normalized_profile

## Product Strategy Meaning

Product Security Tiering creates a bridge between core platform engineering and commercial product planning.

It allows FIP/GAGF products to be grouped by security burden:

Tier 1:
Move fast, demo, validate demand.

Tier 2:
Prepare for enterprise SaaS and SOC 2 readiness.

Tier 3:
Prepare for regulated, healthcare, and sensitive-data customers.

Tier 4:
Prepare for federal, air-gapped, on-prem, and critical infrastructure environments.

This prevents every product from carrying the cost of the highest compliance tier while preserving a path for products that truly need stronger security.

## Product Examples

Assessment Factory Lite:

tier_1_standard_commercial

FIP Governance Diagnostics SaaS:

tier_2_enterprise_secure

FIP Healthcare Readiness Diagnostic:

tier_3_regulated_sensitive

FIP Secure:

tier_4_federal_critical

ESY secure runtime:

tier_4_federal_critical

Personal Friction Assistant:

tier_1_standard_commercial or tier_2_enterprise_secure depending on customer data scope

Game Adaptive Intelligence API:

tier_1_standard_commercial or tier_2_enterprise_secure depending on customer data scope

## Productization Checkpoint

Product Security Tiering indicates that the platform is ready to begin product packaging decisions.

The next product-planning questions are:

Which products are Tier 1 and can move toward demos fastest?

Which products are Tier 2 and need enterprise control readiness?

Which products are Tier 3 or Tier 4 and require careful compliance boundary planning?

Which products should be commercialized first without overloading the engineering roadmap?

## Constitutional Boundary

Product Security Tiering does not certify a product as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It classifies security posture and readiness requirements.

Formal compliance requires policies, controls, evidence, audits, authorization boundaries, and third-party review where applicable.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain product security tier recommendations later, but AI must not override deterministic tier classification without human-approved policy changes.
