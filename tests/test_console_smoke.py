from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_console_page_loads():
    response = client.get("/console")

    assert response.status_code == 200
    assert "GAGF Governance Console" in response.text
    assert "Latest Evidence Source" in response.text
    assert "Ingest GitHub Evidence" in response.text
    assert "GitHub Ingestion Result" in response.text
    assert "Events Processed" in response.text
    assert "Required GitHub Payload Shape" in response.text
    assert "event_name" in response.text
    assert "created_at" in response.text
    assert "Clear Payload" in response.text
    assert "Format Payload" in response.text
    assert "Validate Payload" in response.text
    assert 'id="github_ingest_button"' in response.text
    assert "disabled" in response.text
    assert 'id="github_validation_card" class="card result-card hidden"' in response.text
    assert 'id="github_result_card" class="card result-card hidden"' in response.text
    assert 'id="import_result_card" class="card result-card hidden"' in response.text

def test_console_references_static_assets():
    response = client.get("/console")

    assert response.status_code == 200

    html = response.text

    assert "/static/css/console.css" in html
    assert "/static/js/dashboard.js" in html
    assert "/static/js/snapshots.js" in html
    assert "/static/js/decisions.js" in html
    assert "/static/js/activity.js" in html
    assert "/static/js/upload.js" in html
    assert "/static/js/github_ingest.js" in html
    assert "/static/js/console.js" in html
    assert "Reset Example Payload" in response.text
