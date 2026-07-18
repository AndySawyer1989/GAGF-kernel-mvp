from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_PROPOSAL_PACKAGE_CLOSEOUT.md")


def test_assessment_factory_lite_proposal_package_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_proposal_package_closeout_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "2.0.0" in content
    assert "assessment-factory-lite-proposal-package" in content
    assert "Sprint:" in content
    assert "4.9" in content
    assert "complete" in content
    assert "GET /version" in content


def test_assessment_factory_lite_proposal_package_closeout_names_completed_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Commercial Offer Release" in content
    assert "Proposal Builder" in content
    assert "Proposal Builder Endpoint" in content
    assert "Proposal Builder Documentation" in content
    assert "Proposal HTML View" in content
    assert "Proposal HTML Endpoint" in content
    assert "Proposal HTML Documentation" in content
    assert "Proposal Package Release Marker" in content


def test_assessment_factory_lite_proposal_package_closeout_names_artifacts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteProposalBuilderService" in content
    assert "POST /products/assessment-factory-lite/proposal" in content
    assert "assessment_factory_lite_paid_assessment_proposal" in content

    assert "AssessmentFactoryLiteProposalHTMLService" in content
    assert "POST /products/assessment-factory-lite/proposal/html" in content
    assert "assessment_factory_lite_paid_assessment_proposal_html_view" in content


def test_assessment_factory_lite_proposal_package_closeout_preserves_object_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "proposal builder: 1.9.0 / assessment-factory-lite-commercial-offer" in content
    assert "proposal HTML view: 1.9.0 / assessment-factory-lite-commercial-offer" in content
    assert "assessment offer builder: 1.8.0 / assessment-factory-lite-buyer-conversion" in content
    assert "assessment offer HTML view: 1.8.0 / assessment-factory-lite-buyer-conversion" in content
    assert "buyer walkthrough script: 1.7.0 / assessment-factory-lite-demo-delivery-packaging" in content
    assert "buyer walkthrough HTML view: 1.7.0 / assessment-factory-lite-demo-delivery-packaging" in content
    assert "delivery manifest: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "operator runbook: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "delivery readiness: 1.6.0 / assessment-factory-lite-demo-styling-export" in content
    assert "UI view object: 1.1.0 / assessment-factory-lite-demo-package" in content
    assert "HTML screen object: 1.2.0 / assessment-factory-lite-demo-ui" in content
    assert "scenario menu object: 1.4.0 / assessment-factory-lite-demo-loader" in content
    assert "style token object: 1.5.0 / assessment-factory-lite-demo-usability" in content
    assert "buyer export polish object: 1.5.0 / assessment-factory-lite-demo-usability" in content


def test_assessment_factory_lite_proposal_package_closeout_names_proposal_content():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content
    assert "approval and handoff workflow" in content
    assert "approval_delay" in content
    assert "bounded_friction_assessment" in content
    assert "safe_non_sensitive_workflow_evidence" in content
    assert "assessment_summary" in content
    assert "recommended_next_test" in content
    assert "USD 500 - 2500" in content
    assert "fixed_fee_discovery_assessment" in content


def test_assessment_factory_lite_proposal_package_closeout_names_evidence_deliverables_and_timeline():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "sanitized_workflow_export" in content
    assert "approval_timestamps" in content
    assert "handoff_log" in content
    assert "blocked_work_items" in content
    assert "sanitized_csv" in content
    assert "synthetic_sample" in content
    assert "redacted_export" in content
    assert "manual_summary" in content
    assert "redacted_workflow_export" in content
    assert "manual_workflow_summary" in content
    assert "regulated_health_data" in content
    assert "federal_sensitive_data" in content
    assert "live_security_telemetry" in content

    assert "markdown_or_pdf_ready_summary" in content
    assert "workflow_friction_finding" in content
    assert "recommended_intervention" in content
    assert "short_action_plan" in content
    assert "owner_or_stakeholder" in content

    assert "3_to_5_business_days" in content
    assert "intake" in content
    assert "evidence_review" in content
    assert "diagnostic_summary" in content
    assert "recommendation_review" in content


def test_assessment_factory_lite_proposal_package_closeout_names_assumptions_approvals_and_controls():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "buyer_selects_one_workflow_for_assessment" in content
    assert "buyer_provides_safe_non_sensitive_evidence_only" in content
    assert "operator_reviews_evidence_boundary_before_analysis" in content
    assert "assessment_output_is_reviewed_before_buyer_delivery" in content
    assert "final_price_and_terms_are_operator_approved" in content

    assert "evidence_boundary_approval" in content
    assert "commercial_terms_approval" in content
    assert "buyer_scope_acknowledgement" in content
    assert "Confirm proposed evidence is safe for assessment intake." in content
    assert "Confirm final price, scope, and payment terms." in content
    assert "Confirm workflow boundary and excluded scope." in content

    assert "non_binding_proposal_until_operator_approval" in content
    assert "safe_evidence_boundary_required" in content
    assert "excluded_scope_must_be_visible" in content
    assert "human_review_before_sending" in content


def test_assessment_factory_lite_proposal_package_closeout_preserves_boundaries_and_exclusions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "certification_claims_allowed:" in content
    assert "binding_price_quote_allowed:" in content
    assert "False" in content

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "live_system_integration" in content
    assert "autonomous_remediation" in content
    assert "security_certification" in content
    assert "compliance_audit" in content
    assert "soc_2_audit_claims" in content
    assert "fedramp_or_hipaa_certification_claims" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content
    assert "binding_price_quote" in content
    assert "binding_sales_contract" in content


def test_assessment_factory_lite_proposal_package_closeout_names_html_safety_and_next_direction():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment-factory-lite-paid-assessment-proposal-html-view" in content
    assert "Assessment Factory Lite Proposal" in content
    assert "The proposal HTML renderer escapes dynamic proposal values." in content
    assert "custom buyer context" in content
    assert "custom offer content" in content
    assert "custom proposal content" in content

    assert "Formal Proposal Document Generator" in content
    assert "US-230 — Assessment Factory Lite Formal Proposal Document Service" in content
    assert "formal document that can be shared outside the Operator Workstation" in content
    assert "title, buyer summary, problem statement, assessment scope" in content


def test_assessment_factory_lite_proposal_package_closeout_names_readiness_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Release 2.0.0 does not mean Assessment Factory Lite is production SaaS-ready." in content
    assert "paid-assessment offer and then into a proposal-ready artifact" in content
    assert "The proposal remains non-binding until the operator approves final pricing" in content

    assert (
        "The Assessment Factory Lite Proposal Package release does not certify "
        "products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG "
        "certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
