from pathlib import Path


DOC_PATH = Path("docs/ARCHITECTURAL_DIVERSITY_DIAGNOSTICS.md")


def test_architectural_diversity_document_exists():
    assert DOC_PATH.exists()


def test_architectural_diversity_document_names_core_metrics():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ADI - Architectural Diversity Index" in content
    assert "CRR - Complexity Resilience Ratio" in content
    assert "Mononal Risk Score" in content
    assert "mononal_risk_score = 1.0 - ADI" in content


def test_architectural_diversity_document_names_component_contract():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "component_id" in content
    assert "component_type" in content
    assert "subsystem" in content
    assert "authority_zone" in content
    assert "redundancy_group" in content
    assert "dependencies" in content
    assert "interfaces" in content
    assert "criticality" in content


def test_architectural_diversity_document_names_services():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ArchitecturalDiversityDiagnosticService" in content
    assert "ArchitecturalDiversityTelemetryAdapter" in content
    assert "ArchitecturalDiversityPlatformService" in content


def test_architectural_diversity_document_names_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "POST /governance/architecture/diversity" in content
    assert "GET /governance/architecture/platform" in content


def test_architectural_diversity_document_names_postures_and_statuses():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "adaptive_diverse_architecture" in content
    assert "mixed_resilience_architecture" in content
    assert "concentrated_architecture" in content
    assert "mononal_architecture_risk" in content
    assert "platform_architecture_resilient" in content
    assert "platform_architecture_balanced" in content
    assert "platform_architecture_concentrated" in content
    assert "platform_architecture_mononal_risk" in content


def test_architectural_diversity_document_preserves_kernel_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert (
        "The deterministic GAGF Kernel remains the authoritative decision "
        "and verification layer."
    ) in content
    assert (
        "AI must not override ADI, CRR, or mononal-risk calculations."
    ) in content


