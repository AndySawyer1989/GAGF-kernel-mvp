from backend.app.gagf.source_coverage_service import SourceCoverageService


def test_source_coverage_service_returns_summary():
    summary = SourceCoverageService().get_coverage_summary()

    assert summary["status"] == "ok"
    assert summary["total_sources"] == 7
    assert summary["enabled_sources"] == 7
    assert summary["disabled_sources"] == 0
    assert summary["category_count"] >= 5
    assert summary["trust_tier_count"] >= 2
    assert summary["kernel_role_count"] >= 5


def test_source_coverage_service_includes_health_counts():
    summary = SourceCoverageService().get_coverage_summary()

    assert "health_counts" in summary
    assert summary["health_counts"]["available"] == 7
    assert summary["health_counts"]["disabled"] == 0
    assert summary["health_counts"]["misconfigured"] == 0


def test_source_coverage_service_includes_grouped_views():
    summary = SourceCoverageService().get_coverage_summary()

    assert "categories" in summary
    assert "trust_tiers" in summary
    assert "kernel_roles" in summary

    assert isinstance(summary["categories"], list)
    assert isinstance(summary["trust_tiers"], list)
    assert isinstance(summary["kernel_roles"], list)


def test_source_coverage_service_has_no_coverage_gaps_for_complete_registry():
    summary = SourceCoverageService().get_coverage_summary()

    assert summary["coverage_gaps"] == []


def test_source_coverage_service_detects_custom_health_counts():
    service = SourceCoverageService()

    health_records = [
        {"health": "available"},
        {"health": "available"},
        {"health": "disabled"},
        {"health": "misconfigured"},
    ]

    counts = service.build_health_counts(health_records)

    assert counts["available"] == 2
    assert counts["disabled"] == 1
    assert counts["misconfigured"] == 1