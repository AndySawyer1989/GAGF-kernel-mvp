from backend.app.services.dashboard_service import DashboardService


def test_dashboard_detects_latest_evidence_source_github():
    service = DashboardService()

    snapshot = {"snapshot_id": "github-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "GitHub"


def test_dashboard_detects_latest_evidence_source_servicenow():
    service = DashboardService()

    snapshot = {"snapshot_id": "servicenow-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "ServiceNow"

def test_dashboard_detects_latest_evidence_source_jira():
    service = DashboardService()

    snapshot = {"snapshot_id": "jira-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "Jira"

def test_dashboard_detects_latest_evidence_source_okta():
    service = DashboardService()

    snapshot = {"snapshot_id": "okta-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "Okta"


def test_dashboard_detects_latest_evidence_source_csv():
    service = DashboardService()

    snapshot = {"snapshot_id": "csv-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "CSV"


def test_dashboard_detects_latest_evidence_source_api():
    service = DashboardService()

    snapshot = {"snapshot_id": "api-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "API"


def test_dashboard_detects_latest_evidence_source_none():
    service = DashboardService()

    assert service._detect_latest_evidence_source(None) == "None"


def test_dashboard_detects_latest_evidence_source_fallback():
    service = DashboardService()

    snapshot = {"snapshot_id": "manual-abc123"}

    assert service._detect_latest_evidence_source(snapshot) == "Local / Manual"