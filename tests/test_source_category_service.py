from backend.app.gagf.source_category_service import SourceCategoryService


def test_source_category_service_returns_summary():
    summary = SourceCategoryService().get_category_summary()

    assert summary["status"] == "ok"
    assert summary["category_count"] >= 5
    assert isinstance(summary["categories"], list)


def test_source_category_service_groups_identity_sources():
    summary = SourceCategoryService().get_category_summary()

    categories = {
        category["category"]: category
        for category in summary["categories"]
    }

    assert "identity" in categories
    assert categories["identity"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in categories["identity"]["sources"]
    }

    assert "okta" in source_systems
    assert "entra" in source_systems


def test_source_category_service_groups_endpoint_security_sources():
    summary = SourceCategoryService().get_category_summary()

    categories = {
        category["category"]: category
        for category in summary["categories"]
    }

    assert "endpoint_security" in categories
    assert categories["endpoint_security"]["source_count"] == 2

    source_systems = {
        source["source_system"]
        for source in categories["endpoint_security"]["sources"]
    }

    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_category_service_gets_sources_for_category():
    service = SourceCategoryService()

    sources = service.get_sources_for_category("endpoint_security")
    source_systems = {source["source_system"] for source in sources}

    assert len(sources) == 2
    assert "defender" in source_systems
    assert "sentinelone" in source_systems


def test_source_category_service_returns_empty_list_for_unknown_category():
    service = SourceCategoryService()

    sources = service.get_sources_for_category("unknown-category")

    assert sources == []