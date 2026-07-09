from backend.app.gagf.source_registry import SourceRegistry


class SourceHealthService:
    required_fields = {
        "source_system",
        "display_name",
        "category",
        "ingestion_endpoint",
        "trust_tier",
        "kernel_role",
        "enabled",
    }

    def get_health_summary(self) -> dict:
        sources = SourceRegistry().list_sources()
        health_records = [self.evaluate_source(source) for source in sources]

        healthy_sources = sum(
            1 for source in health_records if source["health"] == "available"
        )

        unhealthy_sources = len(health_records) - healthy_sources

        return {
            "status": "ok",
            "sources_checked": len(health_records),
            "healthy_sources": healthy_sources,
            "unhealthy_sources": unhealthy_sources,
            "sources": health_records,
        }

    def evaluate_source(self, source: dict) -> dict:
        missing_fields = [
            field
            for field in self.required_fields
            if field not in source or source.get(field) in {None, ""}
        ]

        if source.get("enabled") is not True:
            health = "disabled"
        elif missing_fields:
            health = "misconfigured"
        else:
            health = "available"

        return {
            "source_system": source.get("source_system"),
            "display_name": source.get("display_name"),
            "category": source.get("category"),
            "ingestion_endpoint": source.get("ingestion_endpoint"),
            "trust_tier": source.get("trust_tier"),
            "kernel_role": source.get("kernel_role"),
            "enabled": source.get("enabled"),
            "health": health,
            "missing_fields": missing_fields,
        }

from backend.app.gagf.source_registry import SourceRegistry


class SourceHealthService:
    required_fields = {
        "source_system",
        "display_name",
        "category",
        "ingestion_endpoint",
        "trust_tier",
        "kernel_role",
        "enabled",
    }

    def get_health_summary(self) -> dict:
        sources = SourceRegistry().list_sources()
        health_records = [self.evaluate_source(source) for source in sources]

        healthy_sources = sum(
            1 for source in health_records if source["health"] == "available"
        )

        unhealthy_sources = len(health_records) - healthy_sources

        return {
            "status": "ok",
            "sources_checked": len(health_records),
            "healthy_sources": healthy_sources,
            "unhealthy_sources": unhealthy_sources,
            "sources": health_records,
        }

    def evaluate_source(self, source: dict) -> dict:
        missing_fields = [
            field
            for field in self.required_fields
            if field not in source or source.get(field) in {None, ""}
        ]

        if source.get("enabled") is not True:
            health = "disabled"
        elif missing_fields:
            health = "misconfigured"
        else:
            health = "available"

        return {
            "source_system": source.get("source_system"),
            "display_name": source.get("display_name"),
            "category": source.get("category"),
            "ingestion_endpoint": source.get("ingestion_endpoint"),
            "trust_tier": source.get("trust_tier"),
            "kernel_role": source.get("kernel_role"),
            "enabled": source.get("enabled"),
            "health": health,
            "missing_fields": missing_fields,
        }