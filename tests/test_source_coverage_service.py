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


def test_source_coverage_service_returns_gap_summary():
    gap_summary = SourceCoverageService().get_coverage_gaps()

    assert gap_summary["status"] == "ok"
    assert gap_summary["gap_count"] == 0
    assert gap_summary["gaps"] == []


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


def test_source_coverage_service_detects_unhealthy_source_gap():
    service = SourceCoverageService()

    gaps = service.detect_coverage_gaps(
        sources=[{"source_system": "broken-source"}],
        health_summary={
            "unhealthy_sources": 1,
        },
        category_summary={
            "category_count": 1,
        },
        trust_tier_summary={
            "trust_tier_count": 1,
        },
        kernel_role_summary={
            "kernel_role_count": 1,
        },
    )

    gap_types = {gap["gap_type"] for gap in gaps}

    assert "unhealthy_sources_present" in gap_types


def test_source_coverage_service_detects_empty_registry_gap():
    service = SourceCoverageService()

    gaps = service.detect_coverage_gaps(
        sources=[],
        health_summary={
            "unhealthy_sources": 0,
        },
        category_summary={
            "category_count": 0,
        },
        trust_tier_summary={
            "trust_tier_count": 0,
        },
        kernel_role_summary={
            "kernel_role_count": 0,
        },
    )

    gap_types = {gap["gap_type"] for gap in gaps}

    assert "source_registry_empty" in gap_types
    assert "missing_categories" in gap_types
    assert "missing_trust_tiers" in gap_types
    assert "missing_kernel_roles" in gap_types






