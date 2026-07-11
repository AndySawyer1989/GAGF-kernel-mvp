from pathlib import Path


DOC_PATH = Path("docs/GOVERNANCE_DIAGNOSTIC_CHAIN.md")


def test_governance_diagnostic_chain_document_exists():
    assert DOC_PATH.exists()


def test_governance_diagnostic_chain_document_names_core_chain():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "Raw Evidence" in content
    assert "Governance Signal" in content
    assert "Signal Correlation" in content
    assert "Friction Signal" in content
    assert "Governance Debt Indicator" in content
    assert "Intervention Candidate" in content
    assert "Unified Diagnostic Chain" in content


def test_governance_diagnostic_chain_document_names_services():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "GovernanceSignalService" in content
    assert "GovernanceSignalSummaryService" in content
    assert "SignalCorrelationService" in content
    assert "FrictionSignalDetectionService" in content
    assert "GovernanceDebtIndicatorService" in content
    assert "InterventionCandidateService" in content
    assert "GovernanceDiagnosticChainService" in content


def test_governance_diagnostic_chain_document_names_endpoints():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "POST /governance/signals" in content
    assert "POST /governance/signals/summary" in content
    assert "POST /governance/signals/correlations" in content
    assert "POST /governance/friction/signals" in content
    assert "POST /governance/debt/indicators" in content
    assert "POST /governance/interventions/candidates" in content
    assert "POST /governance/diagnostics/chain" in content


def test_governance_diagnostic_chain_document_names_chain_postures():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "none" in content
    assert "low_governance_diagnosis" in content
    assert "moderate_governance_diagnosis" in content
    assert "high_governance_diagnosis" in content
    assert "critical_governance_diagnosis" in content


def test_governance_diagnostic_chain_document_preserves_kernel_boundary():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "The diagnostic chain is advisory to the GAGF Kernel." in content
    assert (
        "The deterministic Kernel remains the authoritative decision and "
        "verification layer."
    ) in content
