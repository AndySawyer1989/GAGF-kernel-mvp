from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_console_page_loads():
    response = client.get("/console")

    assert response.status_code == 200
    assert "GAGF Governance Console" in response.text
    assert "Latest Evidence Source" in response.text
    assert "Ingest GitHub Evidence" in response.text

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
