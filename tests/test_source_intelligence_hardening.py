from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


SOURCE_INTELLIGENCE_ENDPOINTS = [
    "/sources",
    "/sources/defender",
    "/sources/sentinelone",
    "/sources/health",
    "/sources/categories",
    "/sources/categories/endpoint_security",
    "/sources/trust-tiers",
    "/sources/trust-tiers/security",
    "/sources/kernel-roles",
    "/sources/kernel-roles/threat_evidence",
    "/sources/coverage",
    "/sources/coverage/gaps",
]


def test_all_source_intelligence_endpoints_return_success_status_code():
    for endpoint in SOURCE_INTELLIGENCE_ENDPOINTS:
        response = client.get(endpoint)

        assert response.status_code == 200, endpoint


def test_static_source_routes_are_not_captured_by_dynamic_source_detail_route():
    route_expectations = {
        "/sources/health": "sources_checked",
        "/sources/categories": "categories",
        "/sources/trust-tiers": "trust_tiers",
        "/sources/kernel-roles": "kernel_roles",
        "/sources/coverage": "total_sources",
        "/sources/coverage/gaps": "gap_count",
    }

    for endpoint, expected_key in route_expectations.items():
        response = client.get(endpoint)

        assert response.status_code == 200, endpoint

        data = response.json()

        assert data["status"] == "ok", endpoint
        assert expected_key in data, endpoint
        assert data.get("error") != "source_not_found", endpoint


def test_all_registered_sources_have_required_metadata():
    response = client.get("/sources")

    assert response.status_code == 200

    data = response.json()
    required_fields = {
        "source_system",
        "display_name",
        "category",
        "ingestion_endpoint",
        "trust_tier",
        "kernel_role",
        "enabled",
    }

    assert data["status"] == "ok"
    assert len(data["sources"]) == 7

    for source in data["sources"]:
        assert required_fields.issubset(source.keys())
        assert source["source_system"]
        assert source["display_name"]
        assert source["category"]
        assert source["ingestion_endpoint"].startswith("/ingest/")
        assert source["trust_tier"]
        assert source["kernel_role"]
        assert source["enabled"] is True


def test_source_coverage_summary_agrees_with_source_registry():
    sources_response = client.get("/sources")
    coverage_response = client.get("/sources/coverage")

    assert sources_response.status_code == 200
    assert coverage_response.status_code == 200

    sources_data = sources_response.json()
    coverage_data = coverage_response.json()

    assert coverage_data["status"] == "ok"
    assert coverage_data["total_sources"] == len(sources_data["sources"])
    assert coverage_data["enabled_sources"] == len(sources_data["sources"])
    assert coverage_data["disabled_sources"] == 0
    assert coverage_data["coverage_gaps"] == []


def test_category_groupings_cover_all_registered_sources_once():
    sources_response = client.get("/sources")
    categories_response = client.get("/sources/categories")

    assert sources_response.status_code == 200
    assert categories_response.status_code == 200

    registry_sources = {
        source["source_system"]
        for source in sources_response.json()["sources"]
    }

    grouped_sources = []

    for category in categories_response.json()["categories"]:
        for source in category["sources"]:
            grouped_sources.append(source["source_system"])

    assert set(grouped_sources) == registry_sources
    assert len(grouped_sources) == len(registry_sources)


def test_trust_tier_groupings_cover_all_registered_sources_once():
    sources_response = client.get("/sources")
    trust_tiers_response = client.get("/sources/trust-tiers")

    assert sources_response.status_code == 200
    assert trust_tiers_response.status_code == 200

    registry_sources = {
        source["source_system"]
        for source in sources_response.json()["sources"]
    }

    grouped_sources = []

    for trust_tier in trust_tiers_response.json()["trust_tiers"]:
        for source in trust_tier["sources"]:
            grouped_sources.append(source["source_system"])

    assert set(grouped_sources) == registry_sources
    assert len(grouped_sources) == len(registry_sources)


def test_kernel_role_groupings_cover_all_registered_sources_once():
    sources_response = client.get("/sources")
    kernel_roles_response = client.get("/sources/kernel-roles")

    assert sources_response.status_code == 200
    assert kernel_roles_response.status_code == 200

    registry_sources = {
        source["source_system"]
        for source in sources_response.json()["sources"]
    }

    grouped_sources = []

    for kernel_role in kernel_roles_response.json()["kernel_roles"]:
        for source in kernel_role["sources"]:
            grouped_sources.append(source["source_system"])

    assert set(grouped_sources) == registry_sources
    assert len(grouped_sources) == len(registry_sources)


def test_expected_source_intelligence_model_is_present():
    response = client.get("/sources")

    assert response.status_code == 200

    sources = {
        source["source_system"]: source
        for source in response.json()["sources"]
    }

    assert sources["github"]["category"] == "devops"
    assert sources["github"]["trust_tier"] == "operational"
    assert sources["github"]["kernel_role"] == "delivery_evidence"

    assert sources["jira"]["category"] == "work_management"
    assert sources["jira"]["trust_tier"] == "operational"
    assert sources["jira"]["kernel_role"] == "workflow_evidence"

    assert sources["servicenow"]["category"] == "it_service_management"
    assert sources["servicenow"]["trust_tier"] == "operational"
    assert sources["servicenow"]["kernel_role"] == "incident_evidence"

    assert sources["okta"]["category"] == "identity"
    assert sources["okta"]["trust_tier"] == "security"
    assert sources["okta"]["kernel_role"] == "identity_evidence"

    assert sources["entra"]["category"] == "identity"
    assert sources["entra"]["trust_tier"] == "security"
    assert sources["entra"]["kernel_role"] == "identity_evidence"

    assert sources["defender"]["category"] == "endpoint_security"
    assert sources["defender"]["trust_tier"] == "security"
    assert sources["defender"]["kernel_role"] == "threat_evidence"

    assert sources["sentinelone"]["category"] == "endpoint_security"
    assert sources["sentinelone"]["trust_tier"] == "security"
    assert sources["sentinelone"]["kernel_role"] == "threat_evidence"
