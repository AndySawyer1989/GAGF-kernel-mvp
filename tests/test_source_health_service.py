from backend.app.gagf.source_health_service import SourceHealthService


def test_source_health_service_returns_summary():
    summary = SourceHealthService().get_health_summary()

    assert summary["status"] == "ok"
    assert summary["sources_checked"] >= 7
    assert summary["healthy_sources"] >= 7
    assert summary["unhealthy_sources"] == 0
    assert isinstance(summary["sources"], list)


def test_source_health_service_marks_registered_sources_available():
    summary = SourceHealthService().get_health_summary()

    sources_by_system = {
        source["source_system"]: source for source in summary["sources"]
    }

    assert sources_by_system["defender"]["health"] == "available"
    assert sources_by_system["sentinelone"]["health"] == "available"
    assert sources_by_system["okta"]["health"] == "available"
    assert sources_by_system["entra"]["health"] == "available"


def test_source_health_service_includes_required_health_fields():
    summary = SourceHealthService().get_health_summary()

    for source in summary["sources"]:
        assert "source_system" in source
        assert "display_name" in source
        assert "category" in source
        assert "ingestion_endpoint" in source
        assert "trust_tier" in source
        assert "kernel_role" in source
        assert "enabled" in source
        assert "health" in source
        assert "missing_fields" in source


def test_source_health_service_detects_misconfigured_source():
    service = SourceHealthService()

    source = {
        "source_system": "broken-source",
        "display_name": "Broken Source",
        "category": "security",
        "ingestion_endpoint": "",
        "trust_tier": "security",
        "kernel_role": "threat_evidence",
        "enabled": True,
    }

    result = service.evaluate_source(source)

    assert result["health"] == "misconfigured"
    assert "ingestion_endpoint" in result["missing_fields"]


def test_source_health_service_detects_disabled_source():
    service = SourceHealthService()

    source = {
        "source_system": "disabled-source",
        "display_name": "Disabled Source",
        "category": "security",
        "ingestion_endpoint": "/ingest/disabled",
        "trust_tier": "security",
        "kernel_role": "threat_evidence",
        "enabled": False,
    }

    result = service.evaluate_source(source)

    assert result["health"] == "disabled"
    assert result["missing_fields"] == []





