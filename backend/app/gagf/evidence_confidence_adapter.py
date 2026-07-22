from backend.app.gagf.evidence_diagnostics_service import (
    EvidenceDiagnosticsService,
)
from backend.app.gagf.schemas import EvidenceConfidence


EVIDENCE_CONFIDENCE_CALCULATION_ID = "evidence-confidence"
EVIDENCE_CONFIDENCE_CALCULATION_VERSION = "0.1.0-diagnostics"
EVIDENCE_CONFIDENCE_CALCULATION_STATUS = "PROVISIONAL_HEURISTIC"
EVIDENCE_CONFIDENCE_AUTHORITY = "NON_AUTHORITATIVE"


class EvidenceConfidenceAdapter:
    def build_confidence(self, events: list) -> dict:
        diagnostics = EvidenceDiagnosticsService().diagnose_events(events)

        confidence_score = self.calculate_confidence_score(diagnostics)
        confidence_band = self.get_confidence_band(confidence_score)

        conflict_health = self.score_conflict_health(
            diagnostics["conflicts"]
        )
        source_coverage = self.score_source_coverage(
            diagnostics["source_coverage"]
        )

        evidence_confidence = EvidenceConfidence(
            score=confidence_score,
            factors={
                "evidence_quality": diagnostics["quality"][
                    "average_quality_score"
                ],
                "cross_source_agreement": diagnostics["agreement"][
                    "agreement_score"
                ],
                "conflict_health": conflict_health,
                "source_coverage": source_coverage,
                "diagnostic_score": diagnostics["diagnostic_score"],
            },
        )

        return {
            "status": "ok",
            "event_count": diagnostics["event_count"],
            "source_count": diagnostics["agreement"]["source_count"],
            "diagnostic_score": diagnostics["diagnostic_score"],
            "diagnostic_band": diagnostics["diagnostic_band"],
            "confidence_score": confidence_score,
            "confidence_band": confidence_band,
            "supporting_sources": diagnostics["agreement"][
                "supporting_sources"
            ],
            "kernel_roles_present": diagnostics["agreement"][
                "kernel_roles_present"
            ],
            "missing_roles": diagnostics["agreement"]["missing_roles"],
            "evidence_confidence": evidence_confidence,
            "diagnostics": diagnostics,
            "calculation_metadata": self.get_calculation_metadata(),
        }

    def get_calculation_metadata(self) -> dict[str, str]:
        return {
            "calculation_id": EVIDENCE_CONFIDENCE_CALCULATION_ID,
            "calculation_version": EVIDENCE_CONFIDENCE_CALCULATION_VERSION,
            "calculation_status": EVIDENCE_CONFIDENCE_CALCULATION_STATUS,
            "authority": EVIDENCE_CONFIDENCE_AUTHORITY,
        }

    def calculate_confidence_score(self, diagnostics: dict) -> float:
        quality_score = diagnostics["quality"]["average_quality_score"]
        agreement_score = diagnostics["agreement"]["agreement_score"]
        conflict_score = self.score_conflict_health(
            diagnostics["conflicts"]
        )
        coverage_score = self.score_source_coverage(
            diagnostics["source_coverage"]
        )

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

    def get_confidence_band(self, confidence_score: float) -> str:
        if confidence_score >= 0.85:
            return "high"

        if confidence_score >= 0.65:
            return "medium"

        if confidence_score > 0.0:
            return "low"

        return "invalid"
