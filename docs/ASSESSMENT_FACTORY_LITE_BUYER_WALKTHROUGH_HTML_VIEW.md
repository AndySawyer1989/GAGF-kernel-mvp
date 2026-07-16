# Assessment Factory Lite Buyer Walkthrough HTML View

## Purpose

The Assessment Factory Lite Buyer Walkthrough HTML View documents the presentation-ready buyer walkthrough screen.

It turns the buyer walkthrough script into a structured HTML view that the Operator Workstation can render during a live demo.

The view helps the operator present the demo consistently with buyer-facing language, scenario cards, finding explanation, intervention explanation, buyer questions, objection responses, and the demo-only boundary.

## Capability Chain

Assessment Factory Lite Demo Package
→ Buyer Walkthrough Script
→ Buyer Walkthrough HTML View Service
→ Buyer Walkthrough HTML View Endpoint
→ Presentation-Ready HTML
→ Operator Workstation Buyer Demo View

## Service

### AssessmentFactoryLiteBuyerWalkthroughHTMLService

File:

backend/app/gagf/assessment_factory_lite_buyer_walkthrough_html_service.py

Purpose:

Render the buyer walkthrough script as a UI-ready HTML view.

The service returns presentation-ready HTML plus the source script and view section contract.

## Endpoint

### Buyer Walkthrough HTML View Endpoint

GET /products/assessment-factory-lite/buyer-walkthrough/html

Purpose:

Returns the Assessment Factory Lite buyer walkthrough HTML view.

The Operator Workstation can use this endpoint to fetch a presentation-ready buyer walkthrough screen.

## Response Contract

The buyer walkthrough HTML view response includes:

status
view_type
package_name
release
version
view_stage
html
source_script
view_sections
operator_message
recommended_action

## View Type

The view_type value is:

assessment_factory_lite_buyer_walkthrough_html_view

## Release Marker

The buyer walkthrough HTML view object belongs to:

release:

assessment-factory-lite-demo-delivery-packaging

version:

1.7.0

## View Stage

The view_stage value is:

buyer_demo_conversion

## Recommended Action

The recommended_action value is:

present_buyer_walkthrough_html_view

## View Sections

The HTML view includes these sections:

walkthrough_header
opening_script
problem_frame
scenario_script
finding_script
intervention_script
boundary_script
buyer_questions
close_script
objection_responses
demo_boundary

## HTML Document Structure

The HTML output includes:

doctype declaration
html lang attribute
page title
body data-view attribute
header section
script summary section
opening script section
problem frame section
scenario script section
finding script section
intervention script section
boundary script section
buyer questions section
close script section
objection responses section
demo boundary section

The body data-view value is:

assessment-factory-lite-buyer-walkthrough-html-view

The page title is:

Assessment Factory Lite Buyer Walkthrough

## Header Section

The walkthrough header identifies the view as a buyer walkthrough.

It displays:

Buyer Walkthrough
version
Assessment Factory Lite Demo Package
buyer_demo_conversion

## Script Summary Section

The script summary section displays the buyer positioning.

It includes:

delivery mode
conversion goal
positioning statement

The positioning statement is:

Assessment Factory Lite shows where work gets stuck, why it creates drag, and what small operational test to try first.

## Opening Script Section

The opening script section presents the first buyer-facing explanation.

Core buyer language:

This is a sample-data-only demo of Assessment Factory Lite.

The opening script explains that the demo shows how workflow evidence can reveal where work gets stuck, explain the top source of drag, and suggest a focused intervention to test first.

## Problem Frame Section

The problem frame section explains the buyer problem.

Core buyer language:

Most teams feel delays before they can prove them.

The problem frame explains that work waits on approvals, ownership, dependencies, or unclear handoffs, and that Assessment Factory Lite turns those workflow signals into a clear friction finding.

## Scenario Script Section

The scenario script section renders scenario cards.

Included scenarios:

standard
invalid
empty

## Standard Scenario Card

Scenario:

standard

Label:

Approval Delay and Blocked Work

Expected friction:

approval_delay

Purpose:

Show approval delay and blocked work using synthetic workflow rows.

## Invalid Scenario Card

Scenario:

invalid

Label:

Unsafe Data Boundary Test

Expected friction:

none

Purpose:

Show that unsafe sample rows are rejected before buyer-facing findings are produced.

## Empty Scenario Card

Scenario:

empty

Label:

Empty Demo Starting State

Expected friction:

none

Purpose:

Show the empty starting state before sample rows are loaded.

## Finding Script Section

The finding section explains the top friction finding.

Example finding:

Approval delays are creating workflow drag.

Evidence link:

synthetic approval and blocked-work events

Purpose:

Help the buyer understand that the product identifies the constraint, not just the symptoms.

## Intervention Script Section

The intervention section explains the recommended intervention.

Recommended intervention:

streamline_approval_path

Buyer value:

reduce waiting time and make approval ownership clearer

Core explanation:

The recommended intervention does not mean removing accountability.

It means testing a narrow improvement such as clearer ownership, faster routing, or a smaller approval threshold.

## Boundary Script Section

The boundary script section explains the demo-only data boundary.

Core buyer language:

This demo uses synthetic sample data only.

The boundary script warns that the operator should not upload real customer data, regulated data, federal data, secrets, or live security telemetry into this demo path.

## Buyer Questions Section

The buyer questions section includes these question types:

workflow_similarity
evidence_source
first_test
buyer_value

## Workflow Similarity Question

Question:

Which part of this sample workflow most resembles where your team gets stuck?

Purpose:

connect the demo to the buyer's real workflow

## Evidence Source Question

Question:

What safe, non-sensitive workflow evidence could we inspect first?

Purpose:

identify possible assessment inputs

## First Test Question

Question:

If approval delay is the issue, what is the smallest approval-path test worth trying?

Purpose:

move toward a focused assessment or pilot

## Buyer Value Question

Question:

If we could show your top workflow constraint clearly, who would need to see that result?

Purpose:

identify stakeholders and buying path

## Close Script Section

The close script section gives the operator a transition to the assessment offer.

Call to action:

schedule_paid_assessment_conversation

Core language:

The next step would not be a big deployment. It would be a small, bounded assessment using safe evidence to identify one or two high-friction workflow constraints and recommend a focused test.

## Objection Responses Section

The objection responses section includes responses for:

we_do_not_want_to_upload_sensitive_data
we_already_know_where_the_problem_is
this_looks_like_project_management
is_this_production_ready

## Sensitive Data Objection

Objection:

we_do_not_want_to_upload_sensitive_data

Response theme:

The demo is sample-data-only, and a real assessment should start by defining safe evidence boundaries.

## Known Problem Objection

Objection:

we_already_know_where_the_problem_is

Response theme:

The value is turning belief into traceable evidence, ranking the constraint, and choosing the smallest useful intervention.

## Project Management Objection

Objection:

this_looks_like_project_management

Response theme:

Project management tracks work. Assessment Factory Lite focuses on governance friction.

## Production Ready Objection

Objection:

is_this_production_ready

Response theme:

This package is a sample-data-only buyer demo. Production use, regulated data, compliance claims, and live integrations are outside this demo boundary.

## Demo Boundary Section

The demo boundary section displays the demo-only boundary.

Boundary type:

demo_only_sample_data

Allowed data:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events

Prohibited data:

real_customer_data
regulated_data
federal_data
production_customer_data
customer_secrets
live_security_telemetry

certification_claims_allowed:

false

## Styling

The HTML view uses simple inline CSS variables and cards.

Core style tokens include:

afl-brand-orange
afl-brand-gold
afl-brand-purple
afl-surface
afl-surface-alt
afl-text-primary
afl-text-secondary
afl-border-subtle
afl-card-radius
afl-font-family

The view uses card sections, pills, boundary panels, and a walkthrough header.

## Escaping and Safety

The HTML renderer escapes dynamic script values.

This protects the presentation view from rendering raw unsafe markup when custom script content is passed into the renderer.

Escaped values include:

package name
version
script stage
section titles
operator scripts
buyer takeaways
scenario labels
buyer questions
objection text
boundary values

## Relationship to Buyer Walkthrough Script

The buyer walkthrough script defines what the operator should say.

The buyer walkthrough HTML view turns that script into a presentation-ready screen.

The script is the communication source.

The HTML view is the visual presentation layer.

## Relationship to Operator Workstation

The Operator Workstation can use this HTML view as a buyer-facing presentation surface.

The endpoint gives the workstation one API call for the complete buyer walkthrough screen.

## Relationship to Delivery Readiness

The delivery readiness endpoint verifies whether the demo package is ready.

The buyer walkthrough HTML view assumes the package is ready and focuses on presentation.

Readiness answers:

Can we deliver the demo?

The HTML view answers:

Can the operator present the buyer walkthrough clearly?

## Relationship to Assessment Offer

The buyer walkthrough HTML view supports the transition from demo to assessment offer.

It presents the product as a small, bounded, evidence-driven assessment conversation rather than a large production deployment.

## Demo-Only Boundary

The buyer walkthrough HTML view remains demo-only.

It must not be used to imply production readiness, compliance certification, or authorization for real customer data.

## Excluded Scope

The buyer walkthrough HTML view explicitly excludes:

production_customer_data_processing
regulated_data_processing
federal_data_processing
fedramp_or_hipaa_certification_claims
soc_2_audit_claims
wcag_certification_claims
autonomous_remediation
live_customer_integrations
production_customer_deployment
formal_security_authorization
third_party_audit_claims
persistent_file_upload_storage
customer_tenant_storage
pdf_generation
payment_processing
live_customer_remediation
production_workflow_changes
guaranteed_operational_outcomes
binding_consulting_commitments

## Compliance Boundary

The Assessment Factory Lite Buyer Walkthrough HTML View does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic presentation view for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Walkthrough HTML View does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It helps the operator present a deterministic sample-data-only demo while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt presentation language, but AI must not override deterministic demo boundaries without human-approved policy changes.
