from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_architectural_diversity_platform_output_can_feed_manual_diversity_endpoint():
    platform_response = client.get("/governance/architecture/platform")

    assert platform_response.status_code == 200

    platform_data = platform_response.json()
    components = platform_data["components"]

    diversity_response = client.post(
        "/governance/architecture/diversity",
        json=components,
    )

    assert diversity_response.status_code == 200

    diversity_data = diversity_response.json()

    assert diversity_data["status"] == "ok"
    assert diversity_data["component_count"] == platform_data["component_count"]


def test_architectural_diversity_platform_and_manual_scores_match():
    platform_data = client.get(
        "/governance/architecture/platform"
    ).json()

    diversity_data = client.post(
        "/governance/architecture/diversity",
        json=platform_data["components"],
    ).json()

    assert diversity_data["architectural_diversity_index"] == (
        platform_data["architectural_diversity_index"]
    )
    assert diversity_data["complexity_resilience_ratio"] == (
        platform_data["complexity_resilience_ratio"]
    )
    assert diversity_data["mononal_risk_score"] == (
        platform_data["mononal_risk_score"]
    )


def test_architectural_diversity_platform_and_manual_postures_match():
    platform_data = client.get(
        "/governance/architecture/platform"
    ).json()

    diversity_data = client.post(
        "/governance/architecture/diversity",
        json=platform_data["components"],
    ).json()

    assert diversity_data["architecture_posture"] == (
        platform_data["architecture_posture"]
    )
    assert diversity_data["concentration_risk"] == (
        platform_data["concentration_risk"]
    )
    assert diversity_data["dominant_component_type"] == (
        platform_data["dominant_component_type"]
    )


def test_architectural_diversity_platform_and_manual_counts_match():
    platform_data = client.get(
        "/governance/architecture/platform"
    ).json()

    diversity_data = client.post(
        "/governance/architecture/diversity",
        json=platform_data["components"],
    ).json()

    assert diversity_data["component_type_counts"] == (
        platform_data["component_type_counts"]
    )
    assert diversity_data["subsystem_counts"] == (
        platform_data["subsystem_counts"]
    )
    assert diversity_data["authority_zone_counts"] == (
        platform_data["authority_zone_counts"]
    )
    assert diversity_data["redundancy_group_counts"] == (
        platform_data["redundancy_group_counts"]
    )


def test_architectural_diversity_platform_and_manual_breakdowns_match():
    platform_data = client.get(
        "/governance/architecture/platform"
    ).json()

    diversity_data = client.post(
        "/governance/architecture/diversity",
        json=platform_data["components"],
    ).json()

    assert diversity_data["diversity_breakdown"] == (
        platform_data["diversity_breakdown"]
    )


def test_architectural_diversity_platform_components_are_diagnostic_ready():
    platform_data = client.get(
        "/governance/architecture/platform"
    ).json()

    required_component_fields = {
        "component_id",
        "component_type",
        "subsystem",
        "authority_zone",
        "redundancy_group",
        "dependencies",
        "interfaces",
        "criticality",
    }

    for component in platform_data["components"]:
        assert required_component_fields.issubset(component.keys())

    diagnostic_component_ids = {
        diagnostic["component_id"]
        for diagnostic in platform_data["component_diagnostics"]
    }

    component_ids = {
        component["component_id"]
        for component in platform_data["components"]
    }

    assert diagnostic_component_ids == component_ids

