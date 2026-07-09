from backend.app.gagf.source_category_service import SourceCategoryService
from backend.app.gagf.source_health_service import SourceHealthService
from backend.app.gagf.source_kernel_role_service import SourceKernelRoleService
from backend.app.gagf.source_registry import SourceRegistry
from backend.app.gagf.source_trust_tier_service import SourceTrustTierService


class SourceCoverageService:
    def get_coverage_summary(self) -> dict:
        sources = SourceRegistry().list_sources()
        health_summary = SourceHealthService().get_health_summary()
        category_summary = SourceCategoryService().get_category_summary()
        trust_tier_summary = SourceTrustTierService().get_trust_tier_summary()
        kernel_role_summary = SourceKernelRoleService().get_kernel_role_summary()

        enabled_sources = [
            source for source in sources if source.get("enabled") is True
        ]

        disabled_sources = [
            source for source in sources if source.get("enabled") is not True
        ]

        health_counts = self.build_health_counts(health_summary["sources"])
        coverage_gaps = self.detect_coverage_gaps(
            sources=sources,
            health_summary=health_summary,
            category_summary=category_summary,
            trust_tier_summary=trust_tier_summary,
            kernel_role_summary=kernel_role_summary,
        )

        return {
            "status": "ok",
            "total_sources": len(sources),
            "enabled_sources": len(enabled_sources),
            "disabled_sources": len(disabled_sources),
            "category_count": category_summary["category_count"],
            "trust_tier_count": trust_tier_summary["trust_tier_count"],
            "kernel_role_count": kernel_role_summary["kernel_role_count"],
            "health_counts": health_counts,
            "categories": category_summary["categories"],
            "trust_tiers": trust_tier_summary["trust_tiers"],
            "kernel_roles": kernel_role_summary["kernel_roles"],
            "coverage_gaps": coverage_gaps,
        }

    def get_coverage_gaps(self) -> dict:
        coverage_summary = self.get_coverage_summary()
        gaps = coverage_summary["coverage_gaps"]

        return {
            "status": "ok",
            "gap_count": len(gaps),
            "gaps": gaps,
        }

    def build_health_counts(self, health_records: list[dict]) -> dict:
        counts = {
            "available": 0,
            "disabled": 0,
            "misconfigured": 0,
        }

        for source in health_records:
            health = source.get("health", "misconfigured")

            if health not in counts:
                counts[health] = 0

            counts[health] += 1

        return counts

    def detect_coverage_gaps(
        self,
        sources: list[dict],
        health_summary: dict,
        category_summary: dict,
        trust_tier_summary: dict,
        kernel_role_summary: dict,
    ) -> list[dict]:
        gaps = []

        if not sources:
            gaps.append(
                {
                    "gap_type": "source_registry_empty",
                    "severity": "critical",
                    "message": "No sources are registered.",
                }
            )

        if health_summary["unhealthy_sources"] > 0:
            gaps.append(
                {
                    "gap_type": "unhealthy_sources_present",
                    "severity": "warning",
                    "message": "One or more sources are disabled or misconfigured.",
                }
            )

        if category_summary["category_count"] == 0:
            gaps.append(
                {
                    "gap_type": "missing_categories",
                    "severity": "critical",
                    "message": "No source categories are available.",
                }
            )

        if trust_tier_summary["trust_tier_count"] == 0:
            gaps.append(
                {
                    "gap_type": "missing_trust_tiers",
                    "severity": "critical",
                    "message": "No source trust tiers are available.",
                }
            )

        if kernel_role_summary["kernel_role_count"] == 0:
            gaps.append(
                {
                    "gap_type": "missing_kernel_roles",
                    "severity": "critical",
                    "message": "No source kernel roles are available.",
                }
            )

        return gaps