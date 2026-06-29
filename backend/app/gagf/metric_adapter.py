from collections import Counter
from typing import Iterable, List

from backend.app.gagf.schemas import (
    AdaptiveState,
    EvidenceConfidence,
    MetricAdapterResult,
    NormalizationApplied,
    RawSecurityEvent,
    TimestampQuality,
)


NORMALIZATION_DELTAS = {
    "honeyfile_interaction": ("uncertainty", 0.40),
    "failed_auth_burst": ("risk_index", 0.20),
    "unauthorized_api_call": ("risk_index", 0.30),
    "lateral_movement_pattern": ("risk_index", 0.50),
    "containment_success": ("risk_index", -0.40),
    "verification_passed": ("uncertainty", -0.30),
    "service_restored": ("coherence_psi", 0.30),
    "strategy_failure": ("revision_pressure", 0.25),
    "historically_valid_control": ("governance_momentum", 0.20),
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


class MetricAdapter:
    def build_snapshot(self, events: Iterable[RawSecurityEvent]) -> MetricAdapterResult:
        eligible_events = [event for event in events if event.kernel_eligible]

        state = AdaptiveState()
        evidence: List[str] = []
        applied: List[NormalizationApplied] = []

        for event in eligible_events:
            mapping = NORMALIZATION_DELTAS.get(event.event_type)
            if not mapping:
                continue

            indicator, delta = mapping
            current_value = getattr(state, indicator)
            setattr(state, indicator, clamp(current_value + delta))

            evidence.append(event.event_id)
            applied.append(
                NormalizationApplied(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    indicator=indicator,
                    delta=delta,
                )
            )

        confidence = self._calculate_evidence_confidence(eligible_events)

        return MetricAdapterResult(
            adaptive_state=state,
            evidence_confidence=confidence,
            evidence=evidence,
            normalization_applied=applied,
        )

    def _calculate_evidence_confidence(
        self, events: List[RawSecurityEvent]
    ) -> EvidenceConfidence:
        if not events:
            return EvidenceConfidence(
                score=0.0,
                factors={
                    "timestamp_quality": 0.0,
                    "sensor_reliability": 0.0,
                    "cross_source_agreement": 0.0,
                    "telemetry_completeness": 0.0,
                },
            )

        counts = Counter(event.timestamp_quality for event in events)
        total = len(events)

        timestamp_quality_score = (
            counts[TimestampQuality.SOURCE_OCCURRED_AT] * 1.0
            + counts[TimestampQuality.BACKFILLED_FROM_CREATED_AT] * 0.6
            + counts[TimestampQuality.MISSING_TIMESTAMP] * 0.0
        ) / total

        source_systems = {event.source_system for event in events if event.source_system}
        cross_source_agreement = 1.0 if len(source_systems) > 1 else 0.7

        telemetry_completeness = sum(
            1 for event in events if event.event_occurred_at is not None
        ) / total

        sensor_reliability = 0.90

        score = (
            timestamp_quality_score * 0.40
            + sensor_reliability * 0.25
            + cross_source_agreement * 0.20
            + telemetry_completeness * 0.15
        )

        return EvidenceConfidence(
            score=round(clamp(score), 3),
            factors={
                "timestamp_quality": round(timestamp_quality_score, 3),
                "sensor_reliability": sensor_reliability,
                "cross_source_agreement": cross_source_agreement,
                "telemetry_completeness": round(telemetry_completeness, 3),
            },
        )