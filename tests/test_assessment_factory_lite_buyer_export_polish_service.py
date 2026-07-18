from backend.app.gagf.assessment_factory_lite_buyer_export_polish_service import (
    AssessmentFactoryLiteBuyerExportPolishService,
)
from backend.app.gagf.assessment_factory_lite_demo_sample_rows_service import (
    AssessmentFactoryLiteDemoSampleRowsService,
)


def service():
    return AssessmentFactoryLiteBuyerExportPolishService()


def sample_rows(scenario="standard"):
    return AssessmentFactoryLiteDemoSampleRowsService().get_sample_rows(
        scenario
    )["rows"]


def test_assessment_factory_lite_buyer_export_polish_builds_contract():
    result = service().build_polished_export(rows=sample_rows())

    assert result["status"] == "ok"
    assert result["polish_type"] == (
        "assessment_factory_lite_buyer_export_polish"
    )
    assert result["package_name"] == "Assessment Factory Lite Demo Package"
    assert result["release"] == "assessment-factory-lite-demo-usability"
    assert result["version"] == "1.5.0"
    assert result["recommended_action"] == "present_polished_buyer_export"


def test_assessment_factory_lite_buyer_export_polish_creates_buyer_headline_and_summary():
    result = service().build_polished_export(rows=sample_rows())

    assert "workflow" in result["buyer_headline"].lower()
    assert "buyer-facing findings" in result["buyer_summary"]
    assert "synthetic" in result["trust_and_boundary_note"]["summary"]


def test_assessment_factory_lite_buyer_export_polish_creates_key_findings():
    result = service().build_polished_export(rows=sample_rows())

    assert result["key_findings"]
    assert result["key_findings"][0]["finding_type"] == "top_constraint"
    assert result["key_findings"][0]["rank"] == 1
    assert result["key_findings"][0]["title"] == (
        "Approval delays are creating workflow drag"
    )
    assert result["key_findings"][0]["friction_label"] == "approval_delay"


def test_assessment_factory_lite_buyer_export_polish_creates_recommended_intervention():
    result = service().build_polished_export(rows=sample_rows())

    intervention = result["recommended_intervention"]

    assert intervention["intervention_type"] == "streamline_approval_path"
    assert intervention["title"] == "Streamline the approval path"
    assert intervention["buyer_value"] == (
        "Reduce waiting time and make approval ownership clearer."
    )


def test_assessment_factory_lite_buyer_export_polish_creates_next_steps():
    result = service().build_polished_export(rows=sample_rows())

    assert result["next_steps"] == [
        "Review the top friction point with the workflow owner.",
        "Choose one narrow intervention to test first.",
        "Use the demo output to decide what evidence should be collected next.",
    ]


def test_assessment_factory_lite_buyer_export_polish_preserves_source_export_summary():
    result = service().build_polished_export(rows=sample_rows())

    assert result["source_export_summary"]["export_type"] == (
        "assessment_factory_lite_demo_export_summary"
    )
    assert "executive_summary" in result["source_export_summary"]
    assert "recommended_intervention" in result["source_export_summary"]


def test_assessment_factory_lite_buyer_export_polish_rejects_invalid_sample_rows():
    result = service().build_polished_export(rows=sample_rows("invalid"))

    assert result["status"] == "rejected"
    assert result["buyer_headline"] == (
        "Sample data needs repair before buyer presentation."
    )
    assert result["key_findings"][0]["finding_type"] == (
        "sample_data_boundary_failure"
    )
    assert result["recommended_intervention"]["action"] == (
        "repair_sample_csv_before_demo"
    )
    assert result["recommended_action"] == "repair_sample_csv_before_demo"


def test_assessment_factory_lite_buyer_export_polish_preserves_demo_boundary():
    result = service().build_polished_export(rows=sample_rows())
    boundary = result["trust_and_boundary_note"]

    assert boundary["boundary_type"] == "demo_only_sample_data"
    assert boundary["allowed_data"] == [
        "sample_csv",
        "synthetic_workflow_events",
        "mock_approval_events",
        "mock_delay_events",
    ]
    assert boundary["prohibited_data"] == [
        "real_customer_data",
        "regulated_data",
        "federal_data",
        "production_customer_data",
        "customer_secrets",
        "live_security_telemetry",
    ]
    assert boundary["certification_claims_allowed"] is False
