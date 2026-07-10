from itertools import combinations

from backend.app.gagf.governance_signal_service import GovernanceSignalService


class SignalCorrelationService:
    known_relationships = {
        ("identity_friction", "security_risk"): {
            "relationship_type": "access_security_coupling",
            "base_strength": 0.85,
            "governance_interpretation": (
                "Identity friction and security risk are co-occurring, suggesting "
                "access policy, authentication, or authorization pressure may be "
                "contributing to security exposure."
            ),
        },
        ("delivery_friction", "workflow_friction"): {
            "relationship_type": "process_delivery_coupling",
            "base_strength": 0.80,
            "governance_interpretation": (
                "Workflow friction and delivery friction are co-occurring, suggesting "
                "process delay may be slowing software delivery."
            ),
        },
        ("operational_incident", "workflow_friction"): {
            "relationship_type": "process_operations_coupling",
            "base_strength": 0.75,
            "governance_interpretation": (
                "Workflow friction and operational incidents are co-occurring, "
                "suggesting process delay may be affecting service stability."
            ),
        },
        ("delivery_friction", "operational_incident"): {
            "relationship_type": "delivery_operations_coupling",
            "base_strength": 0.75,
            "governance_interpretation": (
                "Delivery friction and operational incidents are co-occurring, "
                "suggesting delivery instability may be affecting operations."
            ),
        },
        ("evidence_conflict", "security_risk"): {
            "relationship_type": "security_evidence_disagreement",
            "base_strength": 0.90,
            "governance_interpretation": (
                "Evidence conflict and security risk are co-occurring, suggesting "
                "security telemetry should be reconciled before confidence increases."
            ),
        },
        ("evidence_conflict", "workflow_friction"): {
            "relationship_type": "workflow_evidence_disagreement",
            "base_strength": 0.80,
            "governance_interpretation": (
                "Evidence conflict and workflow friction are co-occurring, suggesting "
                "process state should be reconciled before governance action."
            ),
        },
        ("evidence_conflict", "identity_friction"): {
            "relationship_type": "identity_evidence_disagreement",
            "base_strength": 0.80,
            "governance_interpretation": (
                "Evidence conflict and identity friction are co-occurring, suggesting "
                "identity claims should be reconciled before confidence increases."
            ),
        },
    }

    def __init__(self, signal_service: GovernanceSignalService | None = None):
        self.signal_service = signal_service or GovernanceSignalService()

    def correlate_events(self, events: list) -> dict:
        classification = self.signal_service.classify_events(events)
        signals = classification["signals"]

        correlations = self.build_correlations(signals)
        correlation_counts = self.build_correlation_counts(correlations)

        return {
            "status": "ok",
            "event_count": classification["event_count"],
            "signal_count": classification["signal_count"],
            "correlation_count": len(correlations),
            "dominant_signal": classification["dominant_signal"],
            "correlation_posture": self.get_correlation_posture(correlations),
            "correlation_counts": correlation_counts,
            "correlations": correlations,
        }

    def build_correlations(self, signals: list[dict]) -> list[dict]:
        correlations = []

        for left, right in combinations(signals, 2):
            left_type = left.get("signal_type", "governance_unknown")
            right_type = right.get("signal_type", "governance_unknown")

            if left_type == "governance_unknown" or right_type == "governance_unknown":
                continue

            if left_type == right_type:
                correlation = self.build_same_signal_correlation(left, right)
            else:
                correlation = self.build_cross_signal_correlation(left, right)

            if correlation is not None:
                correlations.append(correlation)

        return sorted(
            correlations,
            key=lambda correlation: (
                -correlation["correlation_strength"],
                correlation["relationship_type"],
                correlation["left_event_id"] or "",
                correlation["right_event_id"] or "",
            ),
        )

    def build_same_signal_correlation(
        self,
        left: dict,
        right: dict,
    ) -> dict:
        signal_type = left.get("signal_type", "governance_unknown")

        return {
            "left_event_id": left.get("event_id"),
            "right_event_id": right.get("event_id"),
            "left_signal_type": signal_type,
            "right_signal_type": signal_type,
            "relationship_type": "same_signal_cluster",
            "correlation_strength": self.calculate_pair_strength(
                base_strength=0.65,
                left_strength=left.get("signal_strength", 0.0),
                right_strength=right.get("signal_strength", 0.0),
            ),
            "governance_interpretation": (
                f"Multiple {signal_type} signals are present, suggesting a "
                "clustered governance pattern rather than an isolated event."
            ),
        }

    def build_cross_signal_correlation(
        self,
        left: dict,
        right: dict,
    ) -> dict | None:
        left_type = left.get("signal_type", "governance_unknown")
        right_type = right.get("signal_type", "governance_unknown")
        relationship_key = self.normalize_relationship_key(left_type, right_type)
        relationship = self.known_relationships.get(relationship_key)

        if relationship is None:
            return None

        normalized_left_type, normalized_right_type = relationship_key

        ordered_left, ordered_right = self.order_signals_for_relationship(
            left=left,
            right=right,
            normalized_left_type=normalized_left_type,
            normalized_right_type=normalized_right_type,
        )

        return {
            "left_event_id": ordered_left.get("event_id"),
            "right_event_id": ordered_right.get("event_id"),
            "left_signal_type": normalized_left_type,
            "right_signal_type": normalized_right_type,
            "relationship_type": relationship["relationship_type"],
            "correlation_strength": self.calculate_pair_strength(
                base_strength=relationship["base_strength"],
                left_strength=ordered_left.get("signal_strength", 0.0),
                right_strength=ordered_right.get("signal_strength", 0.0),
            ),
            "governance_interpretation": relationship[
                "governance_interpretation"
            ],
        }

    def calculate_pair_strength(
        self,
        base_strength: float,
        left_strength,
        right_strength,
    ) -> float:
        left_value = self.safe_float(left_strength)
        right_value = self.safe_float(right_strength)
        average_signal_strength = (left_value + right_value) / 2

        score = base_strength * 0.60 + average_signal_strength * 0.40

        return round(score, 4)

    def safe_float(self, value) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        return 0.0

    def normalize_relationship_key(
        self,
        left_signal_type: str,
        right_signal_type: str,
    ) -> tuple[str, str]:
        return tuple(sorted([left_signal_type, right_signal_type]))

    def order_signals_for_relationship(
        self,
        left: dict,
        right: dict,
        normalized_left_type: str,
        normalized_right_type: str,
    ) -> tuple[dict, dict]:
        if left.get("signal_type") == normalized_left_type:
            return left, right

        return right, left

    def build_correlation_counts(self, correlations: list[dict]) -> dict:
        counts = {}

        for correlation in correlations:
            relationship_type = correlation.get(
                "relationship_type",
                "unknown",
            )

            if relationship_type not in counts:
                counts[relationship_type] = 0

            counts[relationship_type] += 1

        return dict(sorted(counts.items()))

    def get_correlation_posture(self, correlations: list[dict]) -> str:
        if not correlations:
            return "none"

        max_strength = max(
            correlation["correlation_strength"]
            for correlation in correlations
        )

        if max_strength >= 0.85:
            return "strong_correlation"

        if max_strength >= 0.70:
            return "moderate_correlation"

        return "weak_correlation"