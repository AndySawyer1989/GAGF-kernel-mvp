from backend.app.gagf.governance_debt_indicator_service import (
    GovernanceDebtIndicatorService,
)


class InterventionCandidateService:
    intervention_map = {
        "evidence_debt": {
            "intervention_type": "evidence_reconciliation",
            "base_impact": 0.90,
            "recommended_action": (
                "Reconcile conflicting evidence claims before increasing "
                "confidence or escalating governance action."
            ),
            "governance_interpretation": (
                "Evidence debt should be reduced by improving source agreement, "
                "claim reconciliation, and diagnostic traceability."
            ),
        },
        "security_governance_debt": {
            "intervention_type": "security_policy_review",
            "base_impact": 0.85,
            "recommended_action": (
                "Review security policy, containment workflow, escalation path, "
                "and control ownership."
            ),
            "governance_interpretation": (
                "Security governance debt should be reduced by clarifying "
                "security policy, response authority, and escalation boundaries."
            ),
        },
        "identity_governance_debt": {
            "intervention_type": "access_policy_tuning",
            "base_impact": 0.78,
            "recommended_action": (
                "Tune identity policy, authentication rules, authorization "
                "boundaries, and access exception handling."
            ),
            "governance_interpretation": (
                "Identity governance debt should be reduced by improving access "
                "policy clarity and authentication reliability."
            ),
        },
        "process_governance_debt": {
            "intervention_type": "process_refactor",
            "base_impact": 0.80,
            "recommended_action": (
                "Refactor approval, ownership, dependency, or handoff process "
                "to reduce workflow drag."
            ),
            "governance_interpretation": (
                "Process governance debt should be reduced by removing delay, "
                "ambiguity, and blocked decision paths."
            ),
        },
        "delivery_governance_debt": {
            "intervention_type": "delivery_pipeline_review",
            "base_impact": 0.72,
            "recommended_action": (
                "Review delivery pipeline, merge policy, CI checks, deployment "
                "controls, and review load."
            ),
            "governance_interpretation": (
                "Delivery governance debt should be reduced by improving "
                "software delivery flow and reducing avoidable review drag."
            ),
        },
        "operational_governance_debt": {
            "intervention_type": "operations_stabilization",
            "base_impact": 0.70,
            "recommended_action": (
                "Stabilize operational workflow, incident ownership, change "
                "process, or environment reliability."
            ),
            "governance_interpretation": (
                "Operational governance debt should be reduced by improving "
                "service stability, incident flow, and environment resilience."
            ),
        },
    }

    intervention_priority = [
        "evidence_reconciliation",
        "security_policy_review",
        "access_policy_tuning",
        "process_refactor",
        "delivery_pipeline_review",
        "operations_stabilization",
    ]

    urgency_weights = {
        "immediate": 1.00,
        "near_term": 0.75,
        "monitor": 0.40,
        "none": 0.00,
    }

    def __init__(
        self,
        debt_service: GovernanceDebtIndicatorService | None = None,
    ):
        self.debt_service = debt_service or GovernanceDebtIndicatorService()

    def recommend_events(self, events: list) -> dict:
        debt_result = self.debt_service.assess_events(events)
        intervention_candidates = self.build_intervention_candidates(
            debt_indicators=debt_result["debt_indicators"],
            intervention_urgency=debt_result["intervention_urgency"],
            amplifier_pressure=debt_result["amplifier_pressure"],
        )
        intervention_type_counts = self.build_intervention_type_counts(
            intervention_candidates
        )

        return {
            "status": "ok",
            "event_count": debt_result["event_count"],
            "signal_count": debt_result["signal_count"],
            "friction_signal_count": debt_result["friction_signal_count"],
            "debt_indicator_count": debt_result["debt_indicator_count"],
            "intervention_candidate_count": len(intervention_candidates),
            "dominant_intervention_type": self.get_dominant_intervention_type(
                intervention_type_counts
            ),
            "intervention_posture": self.get_intervention_posture(
                intervention_candidates
            ),
            "recommended_next_action": self.get_recommended_next_action(
                intervention_candidates
            ),
            "governance_debt_score": debt_result["governance_debt_score"],
            "governance_debt_band": debt_result["governance_debt_band"],
            "debt_posture": debt_result["debt_posture"],
            "intervention_urgency": debt_result["intervention_urgency"],
            "amplifier_pressure": debt_result["amplifier_pressure"],
            "intervention_type_counts": intervention_type_counts,
            "intervention_candidates": intervention_candidates,
        }

    def build_intervention_candidates(
        self,
        debt_indicators: list[dict],
        intervention_urgency: str,
        amplifier_pressure: float,
    ) -> list[dict]:
        candidates = []

        for indicator in debt_indicators:
            debt_type = indicator.get("debt_type")
            mapping = self.intervention_map.get(debt_type)

            if mapping is None:
                continue

            priority_score = self.calculate_priority_score(
                base_impact=mapping["base_impact"],
                debt_score=indicator.get("debt_score", 0.0),
                intervention_urgency=intervention_urgency,
                amplifier_pressure=amplifier_pressure,
            )

            candidates.append(
                {
                    "event_id": indicator.get("event_id"),
                    "source_system": indicator.get("source_system"),
                    "source_debt_type": debt_type,
                    "intervention_type": mapping["intervention_type"],
                    "priority_score": priority_score,
                    "priority_band": self.get_priority_band(priority_score),
                    "recommended_action": mapping["recommended_action"],
                    "governance_interpretation": mapping[
                        "governance_interpretation"
                    ],
                }
            )

        return sorted(
            candidates,
            key=lambda record: (
                -record["priority_score"],
                record["intervention_type"],
                record["event_id"] or "",
            ),
        )

    def calculate_priority_score(
        self,
        base_impact: float,
        debt_score,
        intervention_urgency: str,
        amplifier_pressure: float,
    ) -> float:
        debt_value = self.safe_float(debt_score)
        amplifier_value = self.safe_float(amplifier_pressure)
        urgency_value = self.urgency_weights.get(intervention_urgency, 0.0)

        score = (
            base_impact * 0.45
            + debt_value * 0.40
            + urgency_value * 0.10
            + amplifier_value * 0.05
        )

        return round(score, 4)

    def build_intervention_type_counts(
        self,
        intervention_candidates: list[dict],
    ) -> dict:
        counts = {
            "evidence_reconciliation": 0,
            "security_policy_review": 0,
            "access_policy_tuning": 0,
            "process_refactor": 0,
            "delivery_pipeline_review": 0,
            "operations_stabilization": 0,
        }

        for candidate in intervention_candidates:
            intervention_type = candidate.get("intervention_type")

            if intervention_type not in counts:
                counts[intervention_type] = 0

            counts[intervention_type] += 1

        return counts

    def get_dominant_intervention_type(
        self,
        intervention_type_counts: dict,
    ) -> str:
        if (
            not intervention_type_counts
            or sum(intervention_type_counts.values()) == 0
        ):
            return "none"

        max_count = max(intervention_type_counts.values())
        candidates = [
            intervention_type
            for intervention_type, count in intervention_type_counts.items()
            if count == max_count
        ]

        for intervention_type in self.intervention_priority:
            if intervention_type in candidates:
                return intervention_type

        return sorted(candidates)[0]

    def get_intervention_posture(
        self,
        intervention_candidates: list[dict],
    ) -> str:
        if not intervention_candidates:
            return "none"

        max_priority = max(
            candidate["priority_score"]
            for candidate in intervention_candidates
        )

        if max_priority >= 0.80:
            return "immediate_intervention"

        if max_priority >= 0.70:
            return "prioritize_intervention"

        return "monitor_intervention"

    def get_recommended_next_action(
        self,
        intervention_candidates: list[dict],
    ) -> str:
        if not intervention_candidates:
            return "none"

        return intervention_candidates[0]["recommended_action"]

    def get_priority_band(self, priority_score: float) -> str:
        if priority_score >= 0.85:
            return "critical"

        if priority_score >= 0.70:
            return "high"

        if priority_score > 0.0:
            return "moderate"

        return "none"

    def safe_float(self, value) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        return 0.0