from backend.app.gagf.evidence_diagnostics_service import EvidenceDiagnosticsService
from backend.app.gagf.schemas import EvidenceConfidence


class EvidenceConfidenceAdapter:
    def build_confidence(self, events: list) -> dict:
        diagnostics = EvidenceDiagnosticsService().diagnose_events(events)

        confidence_score = self.calculate_confidence_score(diagnostics)
        confidence_band = self.get_confidence_band(confidence_score)

        evidence_confidence = EvidenceConfidence(
            score=confidence_score,
            factors={
                "evidence_quality": diagnostics["quality"]["average_quality_score"],
                "cross_source_agreement": diagnostics["agreement"]["agreement_score"],
                "conflict_health": self.score_conflict_health(
                    diagnostics["conflicts"]
                ),
                "source_coverage": self.score_source_coverage(
                    diagnostics["source_coverage"]
                ),
                "diagnostic_score": diagnostics["diagnostic_score"],
            },
        )

        return {
            "status": "ok",
            "event_count": diagnostics["event_count"],
            "confidence_score": confidence_score,
            "confidence_band": confidence_band,
            "evidence_confidence": evidence_confidence,
            "diagnostics": diagnostics,
        }

    def calculate_confidence_score(self, diagnostics: dict) -> float:
        quality_score = diagnostics["quality"]["average_quality_score"]
        agreement_score = diagnostics["agreement"]["agreement_score"]
        conflict_health = self.score_conflict_health(diagnostics["conflicts"])
        source_coverage = self.score_source_coverage(
            diagnostics["source_coverage"]
        )

        score = (
            quality_score * 0.35
            + agreement_score * 0.30
            + conflict_health * 0.20
            + source_coverage * 0.15
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

    def score_source_coverage(self, source_coverage: dict) -> float:
        total_sources = source_coverage["total_sources"]
        enabled_sources = source_coverage["enabled_sources"]
        coverage_gaps = source_coverage["coverage_gaps"]

        if total_sources == 0:
            return 0.0

        enabled_ratio = enabled_sources / total_sources

        if coverage_gaps:
            return round(enabled_ratio * 0.75, 4)

        return round(enabled_ratio, 4)

    def get_confidence_band(self, confidence_score: float) -> str:
        if confidence_score >= 0.85:
            return "high"

        if confidence_score >= 0.65:
            return "medium"

        if confidence_score > 0.0:
            return "low"

        return "invalid"
