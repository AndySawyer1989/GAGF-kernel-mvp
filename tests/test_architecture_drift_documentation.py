from pathlib import Path


DOC_PATH = Path("docs/ARCHITECTURE_DRIFT_DETECTION.md")


def test_architecture_drift_document_exists():
    assert DOC_PATH.exists()


def test_architecture_drift_document_names_core_drift_metrics():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ADI Drift" in content
    assert "CRR Drift" in content
    assert "Mononal Risk Drift" in content
    assert "architectural_diversity_index_delta" in content
    assert "complexity_resilience_ratio_delta" in content
    assert "mononal_risk_score_delta" in content


def test_architecture_drift_document_names_drift_statuses():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "no_architecture_drift" in content
    assert "low_architecture_drift" in content
    assert "moderate_architecture_drift" in content
    assert "high_architecture_drift" in content
    assert "critical_architecture_drift" in content


def test_architecture_drift_document_names_services():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ArchitectureDriftDetectionService" in content
    assert "ArchitectureDriftDashboardService" in content
    assert "ArchitecturalDiversityPlatformService" in content


def test_architecture_drift_document_names_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "POST /governance/architecture/drift" in content
    assert "POST /governance/architecture/platform/drift" in content
    assert "POST /governance/architecture/drift/dashboard" in content


def test_architecture_drift_document_names_dashboard_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "scorecards" in content
    assert "component_summary" in content
    assert "posture_summary" in content
    assert "risk_summary" in content
    assert "operator_message" in content
    assert "recommended_action" in content


def test_architecture_drift_document_preserves_kernel_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
    assert (
        "AI must not override ADI drift, CRR drift, mononal-risk drift, "
        "posture drift, or deterministic drift status calculations."
    ) in content


