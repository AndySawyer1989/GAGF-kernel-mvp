from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_arbitrate_endpoint_returns_contain():
    response = client.post(
        "/arbitrate",
        json={
            "risk_index": 0.9,
            "uncertainty": 0.8,
            "coherence_psi": 0.85,
            "revision_pressure": 0.1,
            "governance_momentum": 0.5,
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["selected_strategy"] == "Contain"
    assert data["kernel_decision"] == "transition_to_contain"
    assert data["reason"] == ["risk_index_high"]



