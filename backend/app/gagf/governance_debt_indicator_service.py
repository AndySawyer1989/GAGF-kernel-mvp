from backend.app.gagf.friction_signal_detection_service import (
    FrictionSignalDetectionService,
)


class GovernanceDebtIndicatorService:
    debt_map = {
        "evidence_friction": {
            "debt_type": "evidence_debt",
            "base_debt_weight": 0.90,
            "governance_interpretation": (
                "Evidence disagreement is accumulating governance debt because "
                "decisions require reconciliation before trust can increase."
            ),
        },
        "security_pressure": {
            "debt_type": "security_governance_debt",
            "base_debt_weight": 0.85,
            "governance_interpretation": (
                "Security pressure is accumulating governance debt by increasing "
                "review, escalation, containment, or policy burden."
            ),
        },
        "access_friction": {
            "debt_type": "identity_governance_debt",
            "base_debt_weight": 0.78,
            "governance_interpretation": (
                "Identity and access friction is accumulating governance debt "
                "through authentication, authorization, or policy failures."
            ),
        },
        "process_friction": {
            "debt_type": "process_governance_debt",
            "base_debt_weight": 0.80,
            "governance_interpretation": (
                "Process friction is accumulating governance debt through delay, "
                "blockage, dependency wait, or ownership ambiguity."
            ),
        },
        "delivery_friction": {
            "debt_type": "delivery_governance_debt",
            "base_debt_weight": 0.72,
            "governance_interpretation": (
                "Delivery friction is accumulating governance debt through review, "
                "build, merge, or deployment drag."
            ),
        },
        "operational_friction": {
            "debt_type": "operational_governance_debt",
            "base_debt_weight": 0.68,
            "governance_interpretation": (
                "Operational friction is accumulating governance debt through "
                "incident, service, or environment instability."
            ),
        },
    }

    debt_priority = [
        "evidence_debt",
        "security_governance_debt",
        "identity_governance_debt",
        "process_governance_debt",
        "delivery_governance_debt",
        "operational_governance_debt",
    ]

    def __init__(
        self,
        friction_service: FrictionSignalDetectionService | None = None,
    ):
        self.friction_service = friction_service or FrictionSignalDetectionService()

    def assess_events(self, events: list) -> dict:
        friction_result = self.friction_service.detect_events(events)
        debt_indicators = self.build_debt_indicators(
            friction_result["friction_signals"]
        )
        amplifier_pressure = self.calculate_amplifier_pressure(
            friction_result["correlation_amplifiers"]
        )
        debt_type_counts = self.build_debt_type_counts(debt_indicators)
        governance_debt_score = self.calculate_governance_debt_score(
            debt_indicators=debt_indicators,
            amplifier_pressure=amplifier_pressure,
        )

        return {
            "status": "ok",
            "event_count": friction_result["event_count"],
            "signal_count": friction_result["signal_count"],
            "friction_signal_count": friction_result["friction_signal_count"],
            "debt_indicator_count": len(debt_indicators),
            "dominant_debt_type": self.get_dominant_debt_type(debt_type_counts),
            "governance_debt_score": governance_debt_score,
            "governance_debt_band": self.get_governance_debt_band(
                governance_debt_score
            ),
            "debt_posture": self.get_debt_posture(
                governance_debt_score=governance_debt_score,
                amplifier_pressure=amplifier_pressure,
                debt_indicator_count=len(debt_indicators),
            ),
            "intervention_urgency": self.get_intervention_urgency(
                governance_debt_score=governance_debt_score,
                amplifier_pressure=amplifier_pressure,
            ),
            "amplifier_pressure": amplifier_pressure,
            "debt_type_counts": debt_type_counts,
            "debt_indicators": debt_indicators,
        }

    def build_debt_indicators(
        self,
        friction_signals: list[dict],
    ) -> list[dict]:
        debt_indicators = []

        for friction_signal in friction_signals:
            friction_type = friction_signal.get("friction_type")
            mapping = self.debt_map.get(friction_type)

            if mapping is None:
                continue

            debt_score = self.calculate_debt_indicator_score(
                base_debt_weight=mapping["base_debt_weight"],
                friction_intensity=friction_signal.get(
                    "friction_intensity",
                    0.0,
                ),
            )

            debt_indicators.append(
                {
                    "event_id": friction_signal.get("event_id"),
                    "source_system": friction_signal.get("source_system"),
                    "source_friction_type": friction_type,
                    "debt_type": mapping["debt_type"],
                    "debt_score": debt_score,
                    "debt_band": self.get_indicator_debt_band(debt_score),
                    "governance_interpretation": mapping[
                        "governance_interpretation"
                    ],
                }
            )

        return sorted(
            debt_indicators,
            key=lambda record: (
                -record["debt_score"],
                record["debt_type"],
                record["event_id"] or "",
            ),
        )

    def calculate_debt_indicator_score(
        self,
        base_debt_weight: float,
        friction_intensity,
    ) -> float:
        intensity = self.safe_float(friction_intensity)
        score = base_debt_weight * 0.55 + intensity * 0.45

        return round(score, 4)

    def calculate_amplifier_pressure(
        self,
        correlation_amplifiers: list[dict],
    ) -> float:
        if not correlation_amplifiers:
            return 0.0

        strengths = [
            amplifier.get("amplifier_strength", 0.0)
            for amplifier in correlation_amplifiers
            if isinstance(amplifier.get("amplifier_strength", 0.0), (int, float))
        ]

        if not strengths:
            return 0.0

        return round(sum(strengths) / len(strengths), 4)

    def calculate_governance_debt_score(
        self,
        debt_indicators: list[dict],
        amplifier_pressure: float,
    ) -> float:
        if not debt_indicators:
            return 0.0

        debt_scores = [
            indicator.get("debt_score", 0.0)
            for indicator in debt_indicators
            if isinstance(indicator.get("debt_score", 0.0), (int, float))
        ]

        if not debt_scores:
            return 0.0

        average_debt_score = sum(debt_scores) / len(debt_scores)

        if amplifier_pressure <= 0.0:
            return round(average_debt_score, 4)

        score = average_debt_score * 0.80 + amplifier_pressure * 0.20

        return round(score, 4)

    def build_debt_type_counts(self, debt_indicators: list[dict]) -> dict:
        counts = {
            "evidence_debt": 0,
            "security_governance_debt": 0,
            "identity_governance_debt": 0,
            "process_governance_debt": 0,
            "delivery_governance_debt": 0,
            "operational_governance_debt": 0,
        }

        for indicator in debt_indicators:
            debt_type = indicator.get("debt_type")

            if debt_type not in counts:
                counts[debt_type] = 0

            counts[debt_type] += 1

        return counts

    def get_dominant_debt_type(self, debt_type_counts: dict) -> str:
        if not debt_type_counts or sum(debt_type_counts.values()) == 0:
            return "none"

        max_count = max(debt_type_counts.values())
        candidates = [
            debt_type
            for debt_type, count in debt_type_counts.items()
            if count == max_count
        ]

        for debt_type in self.debt_priority:
            if debt_type in candidates:
                return debt_type

        return sorted(candidates)[0]

    def get_indicator_debt_band(self, debt_score: float) -> str:
        if debt_score >= 0.85:
            return "critical"

        if debt_score >= 0.70:
            return "high"

        if debt_score > 0.0:
            return "moderate"

        return "none"

    def get_governance_debt_band(self, governance_debt_score: float) -> str:
        if governance_debt_score >= 0.85:
            return "critical"

        if governance_debt_score >= 0.70:
            return "high"

        if governance_debt_score > 0.0:
            return "moderate"

        return "none"

    def get_debt_posture(
        self,
        governance_debt_score: float,
        amplifier_pressure: float,
        debt_indicator_count: int,
    ) -> str:
        if debt_indicator_count == 0:
            return "none"

        if governance_debt_score >= 0.85 or amplifier_pressure >= 0.85:
            return "critical_debt"

        if governance_debt_score >= 0.70 or amplifier_pressure >= 0.70:
            return "high_debt"

        return "moderate_debt"

    def get_intervention_urgency(
        self,
        governance_debt_score: float,
        amplifier_pressure: float,
    ) -> str:
        if governance_debt_score >= 0.85 or amplifier_pressure >= 0.85:
            return "immediate"

        if governance_debt_score >= 0.70 or amplifier_pressure >= 0.70:
            return "near_term"

        if governance_debt_score > 0.0:
            return "monitor"

        return "none"

    def safe_float(self, value) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        return 0.0