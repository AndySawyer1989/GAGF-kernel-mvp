from backend.app.gagf.friction_signal_detection_service import (
    FrictionSignalDetectionService,
)
from backend.app.gagf.governance_debt_indicator_service import (
    GovernanceDebtIndicatorService,
)
from backend.app.gagf.governance_signal_summary_service import (
    GovernanceSignalSummaryService,
)
from backend.app.gagf.intervention_candidate_service import (
    InterventionCandidateService,
)
from backend.app.gagf.signal_correlation_service import SignalCorrelationService


class GovernanceDiagnosticChainService:
    def __init__(
        self,
        signal_summary_service: GovernanceSignalSummaryService | None = None,
        correlation_service: SignalCorrelationService | None = None,
        friction_service: FrictionSignalDetectionService | None = None,
        debt_service: GovernanceDebtIndicatorService | None = None,
        intervention_service: InterventionCandidateService | None = None,
    ):
        self.signal_summary_service = (
            signal_summary_service or GovernanceSignalSummaryService()
        )
        self.correlation_service = correlation_service or SignalCorrelationService()
        self.friction_service = friction_service or FrictionSignalDetectionService()
        self.debt_service = debt_service or GovernanceDebtIndicatorService()
        self.intervention_service = intervention_service or InterventionCandidateService()

    def diagnose_events(self, events: list) -> dict:
        signal_summary = self.signal_summary_service.summarize_events(events)
        correlation_result = self.correlation_service.correlate_events(events)
        friction_result = self.friction_service.detect_events(events)
        debt_result = self.debt_service.assess_events(events)
        intervention_result = self.intervention_service.recommend_events(events)

        chain_summary = self.build_chain_summary(
            signal_summary=signal_summary,
            correlation_result=correlation_result,
            friction_result=friction_result,
            debt_result=debt_result,
            intervention_result=intervention_result,
        )

        return {
            "status": "ok",
            "event_count": signal_summary["event_count"],
            "chain_stage_count": 5,
            "chain_posture": self.get_chain_posture(chain_summary),
            "recommended_next_action": intervention_result[
                "recommended_next_action"
            ],
            "chain_summary": chain_summary,
            "signal_summary": signal_summary,
            "correlation_result": correlation_result,
            "friction_result": friction_result,
            "debt_result": debt_result,
            "intervention_result": intervention_result,
        }

    def build_chain_summary(
        self,
        signal_summary: dict,
        correlation_result: dict,
        friction_result: dict,
        debt_result: dict,
        intervention_result: dict,
    ) -> dict:
        return {
            "dominant_signal": signal_summary["dominant_signal"],
            "governance_posture": signal_summary["governance_posture"],
            "correlation_posture": correlation_result["correlation_posture"],
            "dominant_friction_type": friction_result[
                "dominant_friction_type"
            ],
            "friction_posture": friction_result["friction_posture"],
            "dominant_debt_type": debt_result["dominant_debt_type"],
            "governance_debt_score": debt_result["governance_debt_score"],
            "governance_debt_band": debt_result["governance_debt_band"],
            "debt_posture": debt_result["debt_posture"],
            "intervention_urgency": debt_result["intervention_urgency"],
            "dominant_intervention_type": intervention_result[
                "dominant_intervention_type"
            ],
            "intervention_posture": intervention_result[
                "intervention_posture"
            ],
            "signal_count": signal_summary["signal_count"],
            "correlation_count": correlation_result["correlation_count"],
            "friction_signal_count": friction_result["friction_signal_count"],
            "debt_indicator_count": debt_result["debt_indicator_count"],
            "intervention_candidate_count": intervention_result[
                "intervention_candidate_count"
            ],
        }

    def get_chain_posture(self, chain_summary: dict) -> str:
        if chain_summary["signal_count"] == 0:
            return "none"

        if (
            chain_summary["debt_posture"] == "critical_debt"
            or chain_summary["intervention_posture"] == "immediate_intervention"
            or chain_summary["governance_debt_band"] == "critical"
        ):
            return "critical_governance_diagnosis"

        if (
            chain_summary["friction_posture"] == "severe_friction"
            or chain_summary["debt_posture"] == "high_debt"
            or chain_summary["intervention_posture"] == "prioritize_intervention"
        ):
            return "high_governance_diagnosis"

        if (
            chain_summary["friction_signal_count"] > 0
            or chain_summary["debt_indicator_count"] > 0
            or chain_summary["intervention_candidate_count"] > 0
        ):
            return "moderate_governance_diagnosis"

        return "low_governance_diagnosis"