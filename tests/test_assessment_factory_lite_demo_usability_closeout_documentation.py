from pathlib import Path


DOC_PATH = Path("docs/ASSESSMENT_FACTORY_LITE_DEMO_USABILITY_CLOSEOUT.md")


def test_assessment_factory_lite_demo_usability_closeout_document_exists():
    assert DOC_PATH.exists()


def test_assessment_factory_lite_demo_usability_closeout_document_names_release_marker():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Release 1.5.0" in content
    assert "assessment-factory-lite-demo-usability" in content
    assert "Sprint" in content
    assert "4.4" in content
    assert "complete" in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_capability_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Demo Package" in content
    assert "Demo Sample Rows Service" in content
    assert "Demo Sample Rows API" in content
    assert "Demo Scenario Menu Service" in content
    assert "Demo Scenario Menu Endpoint" in content
    assert "Demo Scenario Menu Documentation" in content
    assert "HTML Screen Scenario Menu Integration" in content
    assert "Demo Screen Usability Release Marker" in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_services_and_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "AssessmentFactoryLiteDemoSampleRowsService" in content
    assert "AssessmentFactoryLiteDemoScenarioMenuService" in content
    assert "AssessmentFactoryLiteDemoUIHTMLService" in content
    assert "GET /products/assessment-factory-lite/demo-samples/rows" in content
    assert (
        "GET /products/assessment-factory-lite/demo-samples/rows/{scenario}"
        in content
    )
    assert "GET /products/assessment-factory-lite/demo-scenario-menu" in content
    assert "POST /products/assessment-factory-lite/demo-ui/html" in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_menu_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "assessment_factory_lite_demo_scenario_menu" in content
    assert "default_scenario" in content
    assert "menu_items" in content
    assert "aliases" in content
    assert "html_payload" in content
    assert "load_standard_demo_scenario" in content
    assert "load_invalid_boundary_test_scenario" in content
    assert "load_empty_demo_scenario" in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_visible_screen_behavior():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Demo Scenario Menu" in content
    assert "data-scenario" in content
    assert "HTML payload: sample_scenario=standard" in content
    assert "HTML payload: sample_scenario=invalid" in content
    assert "HTML payload: sample_scenario=empty" in content
    assert "Sample Data Loader" in content
    assert "data-sample-scenario" in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_direct_rows_and_toggle():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "sample_rows_result is null" in content
    assert "No canned sample scenario was loaded" in content
    assert "include_scenario_menu" in content
    assert "Scenario menu was not included for this render." in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_internal_contract_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "System release marker:" in content
    assert "1.5.0" in content
    assert "Scenario menu object contract:" in content
    assert "1.4.0" in content
    assert "HTML screen object contract:" in content
    assert "1.2.0" in content
    assert "UI view object contract:" in content
    assert "1.1.0" in content


def test_assessment_factory_lite_demo_usability_closeout_document_names_next_track():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Assessment Factory Lite Buyer-Facing Styling and Export Polish" in content
    assert "US-187 Assessment Factory Lite Demo Screen Style Token Service" in content
    assert "US-188 Assessment Factory Lite Demo Screen Style Token Endpoint" in content
    assert "US-189 Assessment Factory Lite Demo Screen Style Token Documentation" in content
    assert "US-190 Assessment Factory Lite Demo HTML Style Integration" in content
    assert "US-191 Assessment Factory Lite Demo Buyer Export Polish Service" in content
    assert "US-192 Assessment Factory Lite Demo Buyer Export Polish Endpoint" in content
    assert "US-193 Assessment Factory Lite Demo Buyer Export Polish Documentation" in content
    assert "US-194 Assessment Factory Lite Demo Styling and Export Release Marker" in content


def test_assessment_factory_lite_demo_usability_closeout_document_preserves_boundaries():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "demo-only" in content
    assert "sample_csv" in content
    assert "synthetic_workflow_events" in content
    assert "mock_approval_events" in content
    assert "mock_delay_events" in content
    assert "real_customer_data" in content
    assert "regulated_data" in content
    assert "federal_data" in content
    assert "live_security_telemetry" in content
    assert (
        "The Assessment Factory Lite Demo Usability layer does not certify "
        "products as FedRAMP High, HIPAA compliant, or SOC 2 audited."
    ) in content
    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content