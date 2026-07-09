from backend.app.gagf.cross_source_agreement_service import CrossSourceAgreementService
from backend.app.gagf.evidence_conflict_service import EvidenceConflictService
from backend.app.gagf.evidence_quality_service import EvidenceQualityService
from backend.app.gagf.source_coverage_service import SourceCoverageService


class EvidenceDiagnosticsService:
    def diagnose_events(self, events: list) -> dict:
        quality = EvidenceQualityService().score_events(events)
        agreement = CrossSourceAgreementService().evaluate_agreement(events)
        conflicts = EvidenceConflictService().detect_conflicts(events)
        coverage = SourceCoverageService().get_coverage_summary()

        diagnostic_score = self.calculate_diagnostic_score(
            quality=quality,
            agreement=agreement,
            conflicts=conflicts,
            coverage=coverage,
        )

        diagnostic_band = self.get_diagnostic_band(diagnostic_score)

        recommendations = self.build_recommendations(
            quality=quality,
            agreement=agreement,
            conflicts=conflicts,
            coverage=coverage,
        )

        return {
            "status": "ok",
            "event_count": len(events),
            "diagnostic_score": diagnostic_score,
            "diagnostic_band": diagnostic_band,
            "quality": {
                "event_count": quality["event_count"],
                "average_quality_score": quality["average_quality_score"],
                "average_quality_band": quality["average_quality_band"],
            },
            "agreement": {
                "event_count": agreement["event_count"],
                "source_count": agreement["source_count"],
                "agreement_score": agreement["agreement_score"],
                "agreement_band": agreement["agreement_band"],
                "supporting_sources": agreement["supporting_sources"],
                "kernel_roles_present": agreement["kernel_roles_present"],
                "missing_roles": agreement["missing_roles"],
            },
            "conflicts": {
                "event_count": conflicts["event_count"],
                "conflict_count": conflicts["conflict_count"],
                "severity_counts": conflicts["severity_counts"],
                "conflicts": conflicts["conflicts"],
            },
            "source_coverage": {
                "total_sources": coverage["total_sources"],
                "enabled_sources": coverage["enabled_sources"],
                "disabled_sources": coverage["disabled_sources"],
                "coverage_gap_count": len(coverage["coverage_gaps"]),
                "coverage_gaps": coverage["coverage_gaps"],
            },
            "recommendations": recommendations,
        }

    def calculate_diagnostic_score(
        self,
        quality: dict,
        agreement: dict,
        conflicts: dict,
        coverage: dict,
    ) -> float:
        quality_score = quality["average_quality_score"]
        agreement_score = agreement["agreement_score"]
        conflict_score = self.score_conflict_health(conflicts)
        coverage_score = self.score_source_coverage(coverage)

        score = (
            quality_score * 0.35
            + agreement_score * 0.30
            + conflict_score * 0.20
            + coverage_score * 0.15
        )

        return round(score, 4)

    def score_conflict_health(self, conflicts: dict) -> float:
        conflict_count = conflicts["conflict_count"]
        severity_counts = conflicts["severity_counts"]

        if conflict_count == 0:
            return 1.0

        if severity_counts.get("critical", 0) > 0:
            return 0.0

        if severity_counts.get("warning", 0) >= 2:
            return 0.35

        if severity_counts.get("warning", 0) == 1:
            return 0.65

        return 0.75

    def score_source_coverage(self, coverage: dict) -> float:
        total_sources = coverage["total_sources"]
        enabled_sources = coverage["enabled_sources"]
        coverage_gaps = coverage["coverage_gaps"]

        if total_sources == 0:
            return 0.0

        enabled_ratio = enabled_sources / total_sources

        if coverage_gaps:
            return round(enabled_ratio * 0.75, 4)

        return round(enabled_ratio, 4)

    def get_diagnostic_band(self, diagnostic_score: float) -> str:
        if diagnostic_score >= 0.85:
            return "healthy"

        if diagnostic_score >= 0.65:
            return "watch"

        if diagnostic_score > 0.0:
            return "degraded"

        return "invalid"

    def build_recommendations(
        self,
        quality: dict,
        agreement: dict,
        conflicts: dict,
        coverage: dict,
    ) -> list[dict]:
        recommendations = []

        if quality["average_quality_score"] < 0.85:
            recommendations.append(
                {
                    "recommendation_type": "improve_evidence_quality",
                    "severity": "warning",
                    "message": "Improve timestamp quality, source registration, or metadata completeness before relying on this evidence.",
                }
            )

        if agreement["agreement_score"] < 0.60:
            recommendations.append(
                {
                    "recommendation_type": "increase_cross_source_agreement",
                    "severity": "warning",
                    "message": "Add supporting evidence from additional registered sources or kernel roles.",
                }
            )

        if agreement["missing_roles"]:
            recommendations.append(
                {
                    "recommendation_type": "missing_kernel_roles",
                    "severity": "info",
                    "message": "Some expected kernel evidence roles are missing from this event set.",
                    "missing_roles": agreement["missing_roles"],
                }
            )

        if conflicts["conflict_count"] > 0:
            recommendations.append(
                {
                    "recommendation_type": "resolve_evidence_conflicts",
                    "severity": "warning",
                    "message": "Resolve conflicting source claims before increasing confidence.",
                    "conflict_count": conflicts["conflict_count"],
                }
            )

        if coverage["coverage_gaps"]:
            recommendations.append(
                {
                    "recommendation_type": "resolve_source_coverage_gaps",
                    "severity": "warning",
                    "message": "Resolve source registry or source health gaps.",
                    "coverage_gap_count": len(coverage["coverage_gaps"]),
                }
            )

        return recommendations