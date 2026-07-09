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
    assert "Validate the payload before ingesting" in response.text
    assert "Format Payload" in response.text
    assert "Validate Payload" in response.text
    assert 'id="github_ingest_button"' in response.text
    assert "disabled" in response.text
    assert "GitHub Evidence Workflow" in response.text
    assert "Paste or edit the GitHub payload" in response.text
    assert "Ingest Jira Evidence" in response.text
    assert "Required Jira Payload Shape" in response.text
    assert "Jira Evidence Workflow" in response.text
    assert "Jira Payload Validation" in response.text
    assert "Jira Ingestion Result" in response.text
    assert "Ingest Okta Evidence" in response.text
    assert "Required Okta Payload Shape" in response.text
    assert "Okta Evidence Workflow" in response.text
    assert "Okta Payload Validation" in response.text
    assert "Okta Ingestion Result" in response.text
    assert "Ingest Entra ID Evidence" in response.text
    assert "Required Entra ID Payload Shape" in response.text
    assert "Entra ID Evidence Workflow" in response.text
    assert "Entra ID Payload Validation" in response.text
    assert "Entra ID Ingestion Result" in response.text
    assert "Ingest SentinelOne Evidence" in response.text
    assert "Required SentinelOne Payload Shape" in response.text
    assert "SentinelOne Evidence Workflow" in response.text
    assert "SentinelOne Payload Validation" in response.text
    assert "SentinelOne Ingestion Result" in response.text
    assert "Format the payload if needed" in response.text
    assert "Validate the payload" in response.text
    assert "Ingest evidence after validation passes" in response.text
    assert "Review validation and ingestion results" in response.text
    assert 'id="github_validation_card" class="card result-card hidden"' in response.text
    assert 'id="github_result_card" class="card result-card hidden"' in response.text
    assert 'id="import_result_card" class="card result-card hidden"' in response.text
    assert "Ingest ServiceNow Evidence" in response.text
    assert "Required ServiceNow Payload Shape" in response.text
    assert "ServiceNow Evidence Workflow" in response.text
    assert "ServiceNow Payload Validation" in response.text
    assert "ServiceNow Ingestion Result" in response.text

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
    assert "/static/js/servicenow_ingest.js" in html
    assert "/static/js/jira_ingest.js" in html
    assert "/static/js/okta_ingest.js" in html
    assert "/static/js/entra_ingest.js" in html
    assert "/static/js/sentinelone_ingest.js" in html
    assert "/static/js/console.js" in html
    assert "Reset Example Payload" in response.text

def test_github_operator_buttons_are_in_safe_order():
    response = client.get("/console")

    assert response.status_code == 200

    html = response.text

    validate_index = html.index('<button onclick="validateGitHubPayload()">Validate Payload</button>')
    ingest_index = html.index('id="github_ingest_button"')
    format_index = html.index('<button onclick="formatGitHubPayload()">Format Payload</button>')
    reset_index = html.index('<button onclick="resetGitHubExamplePayload()">Reset Example Payload</button>')
    clear_index = html.index('<button onclick="clearGitHubPayload()">Clear Payload</button>')

    assert validate_index < ingest_index
    assert ingest_index < format_index
    assert format_index < reset_index
    assert reset_index < clear_index

def test_console_scripts_use_source_aware_activity_labels():
    github_response = client.get("/static/js/github_ingest.js")
    servicenow_response = client.get("/static/js/servicenow_ingest.js")
    upload_response = client.get("/static/js/upload.js")

    assert github_response.status_code == 200
    assert servicenow_response.status_code == 200
    assert upload_response.status_code == 200

    github_js = github_response.text
    servicenow_js = servicenow_response.text
    upload_js = upload_response.text

    assert "[GitHub] Evidence ingested" in github_js
    assert "[GitHub] Payload validation passed" in github_js

    assert "[ServiceNow] Evidence ingested" in servicenow_js
    assert "[ServiceNow] Payload validation passed" in servicenow_js

    assert "[Kernel] Strategy selected" in github_js
    assert "[Kernel] Strategy selected" in servicenow_js

    assert "[CSV]" in upload_js

def test_jira_ingest_script_has_source_aware_activity_labels():
    response = client.get("/static/js/jira_ingest.js")

    assert response.status_code == 200

    js = response.text

    assert "[Jira] Payload validation passed" in js
    assert "[Jira] Evidence ingested" in js
    assert "[Jira] Snapshot" in js
    assert "[Kernel] Strategy selected" in js

def test_okta_ingest_script_has_source_aware_activity_labels():
    response = client.get("/static/js/okta_ingest.js")

    assert response.status_code == 200

    js = response.text

    assert "[Okta] Payload validation passed" in js
    assert "[Okta] Evidence ingested" in js
    assert "[Okta] Snapshot" in js
    assert "[Kernel] Strategy selected" in js

def test_entra_ingest_script_has_source_aware_activity_labels():
    response = client.get("/static/js/entra_ingest.js")

    assert response.status_code == 200

    js = response.text

    assert "[Entra ID] Payload validation passed" in js
    assert "[Entra ID] Evidence ingested" in js
    assert "[Entra ID] Snapshot" in js
    assert "[Kernel] Strategy selected" in js

def test_sentinelone_ingest_script_has_source_aware_activity_labels():
    response = client.get("/static/js/sentinelone_ingest.js")

    assert response.status_code == 200

    js = response.text

    assert "[SentinelOne] Payload validation passed" in js
    assert "[SentinelOne] Evidence ingested" in js
    assert "[SentinelOne] Snapshot" in js
    assert "[Kernel] Strategy selected" in js