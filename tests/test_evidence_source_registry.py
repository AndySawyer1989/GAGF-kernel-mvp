from backend.app.services.evidence_source_registry import EvidenceSourceRegistry


def test_registry_detects_github_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("github-abc123") == "GitHub"


def test_registry_detects_servicenow_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("servicenow-abc123") == "ServiceNow"


def test_registry_detects_jira_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("jira-abc123") == "Jira"


def test_registry_detects_okta_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("okta-abc123") == "Okta"


def test_registry_detects_entra_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("entra-abc123") == "Entra ID"


def test_registry_detects_sentinelone_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("sentinelone-abc123") == "SentinelOne"

def test_registry_detects_defender_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("defender-abc123") == "Microsoft Defender"

def test_registry_detects_wiz_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("wiz-abc123") == "Wiz"

def test_registry_detects_crowdstrike_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("crowdstrike-abc123") == "CrowdStrike"

def test_registry_detects_csv_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("csv-abc123") == "CSV"


def test_registry_detects_api_snapshot_id():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("api-abc123") == "API"


def test_registry_defaults_unknown_snapshot_id_to_local_manual():
    assert EvidenceSourceRegistry.detect_from_snapshot_id("manual-abc123") == "Local / Manual"


def test_registry_detects_none_snapshot_as_none():
    assert EvidenceSourceRegistry.detect_from_snapshot(None) == "None"


def test_registry_detects_source_from_snapshot_dict():
    snapshot = {"snapshot_id": "servicenow-abc123"}

    assert EvidenceSourceRegistry.detect_from_snapshot(snapshot) == "ServiceNow"