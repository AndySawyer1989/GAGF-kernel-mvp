from backend.app.gagf.architectural_diversity_diagnostic_service import (
    ArchitecturalDiversityDiagnosticService,
)


def test_architectural_diversity_service_returns_empty_result():
    result = ArchitecturalDiversityDiagnosticService().diagnose_components([])

    assert result == {
        "status": "ok",
        "component_count": 0,
        "architectural_diversity_index": 0.0,
        "complexity_resilience_ratio": 0.0,
        "mononal_risk_score": 0.0,
        "architecture_posture": "none",
        "concentration_risk": "none",
        "dominant_component_type": "none",
        "component_type_counts": {},
        "subsystem_counts": {},
        "authority_zone_counts": {},
        "redundancy_group_counts": {},
        "diversity_breakdown": {
            "component_type_diversity": 0.0,
            "subsystem_diversity": 0.0,
            "authority_zone_diversity": 0.0,
            "redundancy_diversity": 0.0,
            "interface_balance_score": 0.0,
        },
        "component_diagnostics": [],
    }


def test_architectural_diversity_service_detects_adaptive_diverse_architecture():
    components = [
        {
            "component_id": "api-1",
            "component_type": "api",
            "subsystem": "interface",
            "authority_zone": "edge",
            "redundancy_group": "api-a",
            "dependencies": ["kernel-1"],
            "interfaces": ["http", "webhook", "console"],
            "criticality": "high",
        },
        {
            "component_id": "worker-1",
            "component_type": "worker",
            "subsystem": "processing",
            "authority_zone": "worker",
            "redundancy_group": "worker-a",
            "dependencies": ["api-1", "ledger-1"],
            "interfaces": ["queue", "events"],
            "criticality": "medium",
        },
        {
            "component_id": "ledger-1",
            "component_type": "ledger",
            "subsystem": "evidence",
            "authority_zone": "ledger",
            "redundancy_group": "ledger-a",
            "dependencies": [],
            "interfaces": ["snapshot", "decision", "diagnostics"],
            "criticality": "critical",
        },
        {
            "component_id": "graph-1",
            "component_type": "graph",
            "subsystem": "topology",
            "authority_zone": "graph",
            "redundancy_group": "graph-a",
            "dependencies": ["ledger-1"],
            "interfaces": ["query", "projection"],
            "criticality": "medium",
        },
    ]

    result = ArchitecturalDiversityDiagnosticService().diagnose_components(
        components
    )

    assert result["status"] == "ok"
    assert result["component_count"] == 4
    assert result["architectural_diversity_index"] == 1.0
    assert result["complexity_resilience_ratio"] == 0.975
    assert result["mononal_risk_score"] == 0.0
    assert result["architecture_posture"] == "adaptive_diverse_architecture"
    assert result["concentration_risk"] == "none"
    assert result["dominant_component_type"] == "ledger"

    assert result["diversity_breakdown"] == {
        "component_type_diversity": 1.0,
        "subsystem_diversity": 1.0,
        "authority_zone_diversity": 1.0,
        "redundancy_diversity": 1.0,
        "interface_balance_score": 0.8333,
    }


def test_architectural_diversity_service_detects_mononal_concentration_risk():
    components = [
        {
            "component_id": "worker-1",
            "component_type": "worker",
            "subsystem": "processing",
            "authority_zone": "worker",
            "redundancy_group": "worker-a",
            "dependencies": ["api-1"],
            "interfaces": ["queue"],
            "criticality": "medium",
        },
        {
            "component_id": "worker-2",
            "component_type": "worker",
            "subsystem": "processing",
            "authority_zone": "worker",
            "redundancy_group": "worker-a",
            "dependencies": ["api-1"],
            "interfaces": ["queue"],
            "criticality": "medium",
        },
        {
            "component_id": "worker-3",
            "component_type": "worker",
            "subsystem": "processing",
            "authority_zone": "worker",
            "redundancy_group": "worker-a",
            "dependencies": ["api-1"],
            "interfaces": ["queue"],
            "criticality": "medium",
        },
        {
            "component_id": "worker-4",
            "component_type": "worker",
            "subsystem": "processing",
            "authority_zone": "worker",
            "redundancy_group": "worker-a",
            "dependencies": ["api-1"],
            "interfaces": ["queue"],
            "criticality": "medium",
        },
    ]

    result = ArchitecturalDiversityDiagnosticService().diagnose_components(
        components
    )

    assert result["component_count"] == 4
    assert result["architectural_diversity_index"] == 0.25
    assert result["complexity_resilience_ratio"] == 0.2625
    assert result["mononal_risk_score"] == 0.75
    assert result["architecture_posture"] == "mononal_architecture_risk"
    assert result["concentration_risk"] == "critical"
    assert result["dominant_component_type"] == "worker"

    assert result["component_type_counts"] == {"worker": 4}
    assert result["subsystem_counts"] == {"processing": 4}
    assert result["authority_zone_counts"] == {"worker": 4}
    assert result["redundancy_group_counts"] == {"worker-a": 4}


def test_architectural_diversity_service_detects_mixed_resilience_architecture():
    components = [
        {
            "component_id": "api-1",
            "component_type": "api",
            "subsystem": "interface",
            "authority_zone": "edge",
            "redundancy_group": "api-a",
            "interfaces": ["http", "webhook"],
        },
        {
            "component_id": "api-2",
            "component_type": "api",
            "subsystem": "interface",
            "authority_zone": "edge",
            "redundancy_group": "api-b",
            "interfaces": ["http", "webhook"],
        },
        {
            "component_id": "ledger-1",
            "component_type": "ledger",
            "subsystem": "evidence",
            "authority_zone": "ledger",
            "redundancy_group": "ledger-a",
            "interfaces": ["snapshot", "decision"],
        },
        {
            "component_id": "ledger-2",
            "component_type": "ledger",
            "subsystem": "evidence",
            "authority_zone": "ledger",
            "redundancy_group": "ledger-b",
            "interfaces": ["snapshot", "decision"],
        },
    ]

    result = ArchitecturalDiversityDiagnosticService().diagnose_components(
        components
    )

    assert result["architectural_diversity_index"] == 0.625
    assert result["complexity_resilience_ratio"] == 0.725
    assert result["mononal_risk_score"] == 0.375
    assert result["architecture_posture"] == "mixed_resilience_architecture"
    assert result["concentration_risk"] == "moderate"
    assert result["dominant_component_type"] == "ledger"


def test_architectural_diversity_service_normalizes_alias_fields():
    components = [
        {
            "id": "Kernel 1",
            "type": "Kernel",
            "domain": "Decision Layer",
            "decision_authority": "Kernel Zone",
            "partition": "Partition A",
            "dependencies": "ledger-1",
            "interfaces": ("policy", "decision"),
            "criticality": "critical",
        }
    ]

    result = ArchitecturalDiversityDiagnosticService().diagnose_components(
        components
    )

    diagnostic = result["component_diagnostics"][0]

    assert diagnostic["component_id"] == "kernel_1"
    assert diagnostic["component_type"] == "kernel"
    assert diagnostic["subsystem"] == "decision_layer"
    assert diagnostic["authority_zone"] == "kernel_zone"
    assert diagnostic["redundancy_group"] == "partition_a"
    assert diagnostic["dependency_count"] == 1
    assert diagnostic["interface_count"] == 2
    assert diagnostic["criticality"] == "critical"


def test_architectural_diversity_service_calculates_component_complexity():
    components = [
        {
            "component_id": "sequencer-1",
            "component_type": "sequencer",
            "subsystem": "ordering",
            "authority_zone": "sequencer",
            "dependencies": ["ledger-1", "kernel-1"],
            "interfaces": ["sequence", "receipt", "fence"],
            "criticality": "critical",
        }
    ]

    result = ArchitecturalDiversityDiagnosticService().diagnose_components(
        components
    )

    diagnostic = result["component_diagnostics"][0]

    assert diagnostic["dependency_count"] == 2
    assert diagnostic["interface_count"] == 3
    assert diagnostic["local_complexity_score"] == 0.89


def test_architectural_diversity_service_orders_dominant_type_by_priority_on_tie():
    service = ArchitecturalDiversityDiagnosticService()

    counts = {
        "worker": 1,
        "ledger": 1,
        "api": 1,
    }

    assert service.get_dominant_value(
        counts,
        service.component_type_priority,
    ) == "ledger"


def test_architectural_diversity_service_classifies_concentration_risk_bands():
    service = ArchitecturalDiversityDiagnosticService()

    assert service.get_concentration_risk(0.0) == "none"
    assert service.get_concentration_risk(0.2) == "low"
    assert service.get_concentration_risk(0.3) == "moderate"
    assert service.get_concentration_risk(0.6) == "high"
    assert service.get_concentration_risk(0.8) == "critical"


def test_architectural_diversity_service_classifies_architecture_postures():
    service = ArchitecturalDiversityDiagnosticService()

    assert service.get_architecture_posture(0.0, 0.0) == "none"
    assert service.get_architecture_posture(
        0.8,
        0.8,
    ) == "adaptive_diverse_architecture"
    assert service.get_architecture_posture(
        0.6,
        0.6,
    ) == "mixed_resilience_architecture"
    assert service.get_architecture_posture(
        0.4,
        0.3,
    ) == "concentrated_architecture"
    assert service.get_architecture_posture(
        0.2,
        0.2,
    ) == "mononal_architecture_risk"


