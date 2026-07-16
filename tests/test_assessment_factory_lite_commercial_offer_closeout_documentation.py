from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_COMMERCIAL_OFFER_CLOSEOUT.md")


def test_assessment_factory_lite_commercial_offer_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_commercial_offer_closeout_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "1.9.0" in content
    assert "assessment-factory-lite-commercial-offer" in content
    assert "Sprint:" in content
    assert "4.8" in content
    assert "complete" in content
    assert "GET /version" in content


def test_assessment_factory_lite_commercial_offer_closeout_names_completed_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Buyer Conversion Release" in content
    assert "Assessment Offer Builder" in content
    assert "Assessment Offer Endpoint" in content
    assert "Assessment Offer Builder Documentation" in content
    assert "Assessment Offer HTML View" in content
    assert "Assessment Offer HTML Endpoint" in content
    assert "Assessment Offer HTML Documentation" in content
    assert "Commercial Offer Release Marker" in content


def test_assessment_factory_lite_commercial_offer_closeout_names_artifacts():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteOfferBuilderService" in content
    assert "POST /products/assessment-factory-lite/assessment-offer" in content
    assert "assessment_factory_lite_paid_assessment_offer" in content

    assert "AssessmentFactoryLiteOfferHTMLService" in content
    assert "POST /products/assessment-factory-lite/assessment-offer/html" in content
    assert "assessment_factory_lite_paid_assessment_offer_html_view" in content


def test_assessment_factory_lite_commercial_offer_closeout_preserves_object_contracts():
    content = DOC_PATH.read_text(encoding="utf-8")

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


def test_assessment_factory_lite_commercial_offer_closeout_names_offer_content():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "operations_leader" in content
    assert "it_manager" in content
    assert "workflow_owner" in content
    assert "founder_operator" in content
    assert "approval delays, ownership gaps, handoff delays, and workflow drag" in content
    assert "approval and handoff workflow" in content
    assert "approval_delay" in content
    assert "safe_non_sensitive_workflow_evidence" in content
    assert "bounded_friction_assessment" in content
    assert "assessment_factory_lite_buyer_summary" in content
    assert "USD 500 - 2500" in content
    assert "fixed_fee_discovery_assessment" in content


def test_assessment_factory_lite_commercial_offer_closeout_names_commitment_controls_and_html():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "small_bounded_assessment" in content
    assert "one_workflow_to_assess" in content
    assert "safe_non_sensitive_evidence" in content
    assert "workflow_owner_contact" in content
    assert "review_time_for_findings" in content

    assert "workflow_similarity" in content
    assert "evidence_source" in content
    assert "first_test" in content
    assert "buyer_value" in content

    assert "sample_or_redacted_data_only" in content
    assert "operator_price_approval" in content
    assert "excluded_scope_visibility" in content
    assert "human_review_before_delivery" in content

    assert "offer_header" in content
    assert "recommended_price_band" in content
    assert "demo_boundary" in content
    assert "excluded_scope" in content
    assert "The assessment offer HTML renderer escapes dynamic offer values." in content


def test_assessment_factory_lite_commercial_offer_closeout_preserves_boundaries_and_exclusions():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo_and_assessment_intake_boundary" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "sanitized_csv" in content
    assert "redacted_workflow_export" in content
    assert "manual_workflow_summary" in content

    assert "real_customer_secrets" in content
    assert "regulated_health_data" in content
    assert "federal_sensitive_data" in content
    assert "production_customer_data_without_review" in content
    assert "credentials" in content
    assert "live_security_telemetry" in content
    assert "certification_claims_allowed:" in content
    assert "binding_price_quote_allowed:" in content
    assert "false" in content

    assert "production_customer_data_processing" in content
    assert "regulated_data_processing" in content
    assert "federal_data_processing" in content
    assert "guaranteed_operational_outcomes" in content
    assert "binding_legal_or_compliance_advice" in content
    assert "binding_price_quote" in content
    assert "binding_sales_contract" in content


def test_assessment_factory_lite_commercial_offer_closeout_names_next_direction_and_constitutional_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Proposal Builder Service" in content
    assert "US-222 — Assessment Factory Lite Proposal Builder Service" in content
    assert "The next bottleneck is turning the offer into a proposal-ready artifact" in content
    assert "commercial terms placeholder" in content
    assert "approval requirements" in content

    assert (
        "The Assessment Factory Lite Commercial Offer release does not "
        "certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, "
        "WCAG certified, or production-ready."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content