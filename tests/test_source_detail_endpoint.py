from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_source_detail_endpoint_returns_defender_metadata():
    response = client.get("/sources/defender")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["source"]["source_system"] == "defender"
    assert data["source"]["display_name"] == "Microsoft Defender"
    assert data["source"]["category"] == "endpoint_security"
    assert data["source"]["ingestion_endpoint"] == "/ingest/defender"
    assert data["source"]["trust_tier"] == "security"
    assert data["source"]["kernel_role"] == "threat_evidence"
    assert data["source"]["enabled"] is True


def test_source_detail_endpoint_returns_sentinelone_metadata():
    response = client.get("/sources/sentinelone")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["source"]["source_system"] == "sentinelone"
    assert data["source"]["display_name"] == "SentinelOne"
    assert data["source"]["category"] == "endpoint_security"
    assert data["source"]["ingestion_endpoint"] == "/ingest/sentinelone"
    assert data["source"]["trust_tier"] == "security"
    assert data["source"]["kernel_role"] == "threat_evidence"
    assert data["source"]["enabled"] is True


def test_source_detail_endpoint_returns_okta_metadata():
    response = client.get("/sources/okta")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["source"]["source_system"] == "okta"
    assert data["source"]["display_name"] == "Okta"
    assert data["source"]["category"] == "identity"
    assert data["source"]["ingestion_endpoint"] == "/ingest/okta"
    assert data["source"]["trust_tier"] == "security"
    assert data["source"]["kernel_role"] == "identity_evidence"
    assert data["source"]["enabled"] is True


def test_source_detail_endpoint_returns_failure_for_unknown_source():
    response = client.get("/sources/unknown-source")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "failed"
    assert data["error"] == "source_not_found"
    assert data["source_system"] == "unknown-source"
