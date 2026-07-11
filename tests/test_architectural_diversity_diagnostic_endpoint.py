from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_architectural_diversity_endpoint_returns_empty_result():
    response = client.post(
        "/governance/architecture/diversity",
        json=[],
    )

    assert response.status_code == 200

    assert response.json() == {
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


def test_architectural_diversity_endpoint_detects_adaptive_diverse_architecture():
    response = client.post(
        "/governance/architecture/diversity",
        json=[
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
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["component_count"] == 4
    assert data["architectural_diversity_index"] == 1.0
    assert data["complexity_resilience_ratio"] == 0.975
    assert data["mononal_risk_score"] == 0.0
    assert data["architecture_posture"] == "adaptive_diverse_architecture"
    assert data["concentration_risk"] == "none"
    assert data["dominant_component_type"] == "ledger"


def test_architectural_diversity_endpoint_detects_mononal_concentration_risk():
    response = client.post(
        "/governance/architecture/diversity",
        json=[
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
        ],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["component_count"] == 4
    assert data["architectural_diversity_index"] == 0.25
    assert data["complexity_resilience_ratio"] == 0.2625
    assert data["mononal_risk_score"] == 0.75
    assert data["architecture_posture"] == "mononal_architecture_risk"
    assert data["concentration_risk"] == "critical"
    assert data["dominant_component_type"] == "worker"


def test_architectural_diversity_endpoint_normalizes_alias_fields():
    response = client.post(
        "/governance/architecture/diversity",
        json=[
            {
                "id": "Kernel 1",
                "type": "Kernel",
                "domain": "Decision Layer",
                "decision_authority": "Kernel Zone",
                "partition": "Partition A",
                "dependencies": "ledger-1",
                "interfaces": ["policy", "decision"],
                "criticality": "critical",
            }
        ],
    )

    assert response.status_code == 200

    diagnostic = response.json()["component_diagnostics"][0]

    assert diagnostic["component_id"] == "kernel_1"
    assert diagnostic["component_type"] == "kernel"
    assert diagnostic["subsystem"] == "decision_layer"
    assert diagnostic["authority_zone"] == "kernel_zone"
    assert diagnostic["redundancy_group"] == "partition_a"
    assert diagnostic["dependency_count"] == 1
    assert diagnostic["interface_count"] == 2
    assert diagnostic["criticality"] == "critical"


def test_architectural_diversity_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/diversity" in actual_routes


def test_architectural_diversity_endpoint_preserves_current_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "0.7.0",
        "release": "architectural-diversity-diagnostics",
        "sprint": "3.6",
        "status": "complete",
    }