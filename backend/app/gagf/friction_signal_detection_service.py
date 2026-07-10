from backend.app.gagf.governance_signal_service import GovernanceSignalService
from backend.app.gagf.signal_correlation_service import SignalCorrelationService


class FrictionSignalDetectionService:
    friction_map = {
        "evidence_conflict": {
            "friction_type": "evidence_friction",
            "base_intensity": 0.85,
            "governance_interpretation": (
                "Evidence disagreement is creating governance drag because "
                "the system cannot safely increase confidence until claims "
                "are reconciled."
            ),
        },
        "security_risk": {
            "friction_type": "security_pressure",
            "base_intensity": 0.80,
            "governance_interpretation": (
                "Security risk is creating governance pressure that may require "
                "review, containment, or escalation."
            ),
        },
        "identity_friction": {
            "friction_type": "access_friction",
            "base_intensity": 0.72,
            "governance_interpretation": (
                "Identity or access failures are creating friction around "
                "authentication, authorization, or policy enforcement."
            ),
        },
        "workflow_friction": {
            "friction_type": "process_friction",
            "base_intensity": 0.75,
            "governance_interpretation": (
                "Workflow delay or blockage is creating process friction in "
                "the governance path."
            ),
        },
        "delivery_friction": {
            "friction_type": "delivery_friction",
            "base_intensity": 0.70,
            "governance_interpretation": (
                "Development, review, build, merge, or deployment activity is "
                "creating delivery friction."
            ),
        },
        "operational_incident": {
            "friction_type": "operational_friction",
            "base_intensity": 0.65,
            "governance_interpretation": (
                "Operational instability is creating service or environment "
                "friction."
            ),
        },
    }

    friction_priority = [
        "evidence_friction",
        "security_pressure",
        "access_friction",
        "process_friction",
        "delivery_friction",
        "operational_friction",
    ]

    def __init__(
        self,
        signal_service: GovernanceSignalService | None = None,
        correlation_service: SignalCorrelationService | None = None,
    ):
        self.signal_service = signal_service or GovernanceSignalService()
        self.correlation_service = correlation_service or SignalCorrelationService(
            signal_service=self.signal_service
        )

    def detect_events(self, events: list) -> dict:
        classification = self.signal_service.classify_events(events)
        correlation_result = self.correlation_service.correlate_events(events)

        friction_signals = self.build_friction_signals(
            classification["signals"]
        )
        correlation_amplifiers = self.build_correlation_amplifiers(
            correlation_result["correlations"]
        )
        friction_type_counts = self.build_friction_type_counts(friction_signals)
        average_friction_intensity = self.average_friction_intensity(
            friction_signals
        )

        return {
            "status": "ok",
            "event_count": classification["event_count"],
            "signal_count": classification["signal_count"],
            "friction_signal_count": len(friction_signals),
            "dominant_friction_type": self.get_dominant_friction_type(
                friction_type_counts
            ),
            "friction_posture": self.get_friction_posture(
                friction_signals=friction_signals,
                correlation_amplifiers=correlation_amplifiers,
                average_friction_intensity=average_friction_intensity,
            ),
            "average_friction_intensity": average_friction_intensity,
            "friction_type_counts": friction_type_counts,
            "correlation_amplifier_count": len(correlation_amplifiers),
            "correlation_amplifiers": correlation_amplifiers,
            "friction_signals": friction_signals,
        }

    def build_friction_signals(self, signals: list[dict]) -> list[dict]:
        friction_signals = []

        for signal in signals:
            signal_type = signal.get("signal_type", "governance_unknown")
            mapping = self.friction_map.get(signal_type)

            if mapping is None:
                continue

            friction_signal = {
                "event_id": signal.get("event_id"),
                "source_system": signal.get("source_system"),
                "source_signal_type": signal_type,
                "friction_type": mapping["friction_type"],
                "friction_intensity": self.calculate_friction_intensity(
                    base_intensity=mapping["base_intensity"],
                    signal_strength=signal.get("signal_strength", 0.0),
                ),
                "friction_band": None,
                "governance_interpretation": mapping[
                    "governance_interpretation"
                ],
            }

            friction_signal["friction_band"] = self.get_friction_band(
                friction_signal["friction_intensity"]
            )

            friction_signals.append(friction_signal)

        return sorted(
            friction_signals,
            key=lambda record: (
                -record["friction_intensity"],
                record["friction_type"],
                record["event_id"] or "",
            ),
        )

    def build_correlation_amplifiers(
        self,
        correlations: list[dict],
    ) -> list[dict]:
        amplifiers = []

        for correlation in correlations:
            strength = correlation.get("correlation_strength", 0.0)

            if not isinstance(strength, (int, float)) or strength < 0.70:
                continue

            amplifiers.append(
                {
                    "relationship_type": correlation.get("relationship_type"),
                    "left_event_id": correlation.get("left_event_id"),
                    "right_event_id": correlation.get("right_event_id"),
                    "amplifier_strength": strength,
                    "amplifier_band": self.get_amplifier_band(strength),
                    "governance_interpretation": (
                        "Correlated governance signals may amplify friction "
                        "beyond the impact of any single event."
                    ),
                }
            )

        return sorted(
            amplifiers,
            key=lambda record: (
                -record["amplifier_strength"],
                record["relationship_type"] or "",
                record["left_event_id"] or "",
                record["right_event_id"] or "",
            ),
        )

    def calculate_friction_intensity(
        self,
        base_intensity: float,
        signal_strength,
    ) -> float:
        strength = self.safe_float(signal_strength)
        score = base_intensity * 0.60 + strength * 0.40

        return round(score, 4)

    def average_friction_intensity(self, friction_signals: list[dict]) -> float:
        if not friction_signals:
            return 0.0

        values = [
            signal.get("friction_intensity", 0.0)
            for signal in friction_signals
            if isinstance(signal.get("friction_intensity", 0.0), (int, float))
        ]

        if not values:
            return 0.0

        return round(sum(values) / len(values), 4)

    def build_friction_type_counts(self, friction_signals: list[dict]) -> dict:
        counts = {
            "evidence_friction": 0,
            "security_pressure": 0,
            "access_friction": 0,
            "process_friction": 0,
            "delivery_friction": 0,
            "operational_friction": 0,
        }

        for signal in friction_signals:
            friction_type = signal.get("friction_type")

            if friction_type not in counts:
                counts[friction_type] = 0

            counts[friction_type] += 1

        return counts

    def get_dominant_friction_type(self, friction_type_counts: dict) -> str:
        if not friction_type_counts or sum(friction_type_counts.values()) == 0:
            return "none"

        max_count = max(friction_type_counts.values())
        candidates = [
            friction_type
            for friction_type, count in friction_type_counts.items()
            if count == max_count
        ]

        for friction_type in self.friction_priority:
            if friction_type in candidates:
                return friction_type

        return sorted(candidates)[0]

    def get_friction_posture(
        self,
        friction_signals: list[dict],
        correlation_amplifiers: list[dict],
        average_friction_intensity: float,
    ) -> str:
        if not friction_signals:
            return "none"

        max_intensity = max(
            signal["friction_intensity"]
            for signal in friction_signals
        )

        max_amplifier = 0.0

        if correlation_amplifiers:
            max_amplifier = max(
                amplifier["amplifier_strength"]
                for amplifier in correlation_amplifiers
            )

        if max_intensity >= 0.85 or max_amplifier >= 0.85:
            return "severe_friction"

        if average_friction_intensity >= 0.75 or max_amplifier >= 0.70:
            return "high_friction"

        if average_friction_intensity > 0.0:
            return "moderate_friction"

        return "none"

    def get_friction_band(self, friction_intensity: float) -> str:
        if friction_intensity >= 0.85:
            return "severe"

        if friction_intensity >= 0.70:
            return "high"

        if friction_intensity > 0.0:
            return "moderate"

        return "none"

    def get_amplifier_band(self, amplifier_strength: float) -> str:
        if amplifier_strength >= 0.85:
            return "strong"

        if amplifier_strength >= 0.70:
            return "moderate"

        return "weak"

    def safe_float(self, value) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        return 0.0