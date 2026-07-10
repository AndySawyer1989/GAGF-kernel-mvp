from backend.app.gagf.governance_signal_service import GovernanceSignalService


class GovernanceSignalSummaryService:
    def __init__(self, signal_service: GovernanceSignalService | None = None):
        self.signal_service = signal_service or GovernanceSignalService()

    def summarize_events(self, events: list) -> dict:
        classification = self.signal_service.classify_events(events)
        signals = classification["signals"]

        average_signal_strength = self.average_signal_strength(signals)
        source_distribution = self.build_source_distribution(signals)
        high_strength_signals = self.get_high_strength_signals(signals)
        governance_posture = self.get_governance_posture(
            dominant_signal=classification["dominant_signal"],
            average_signal_strength=average_signal_strength,
            high_strength_count=len(high_strength_signals),
            signal_counts=classification["signal_counts"],
        )

        return {
            "status": "ok",
            "event_count": classification["event_count"],
            "signal_count": classification["signal_count"],
            "dominant_signal": classification["dominant_signal"],
            "governance_posture": governance_posture,
            "average_signal_strength": average_signal_strength,
            "signal_counts": classification["signal_counts"],
            "source_distribution": source_distribution,
            "high_strength_signal_count": len(high_strength_signals),
            "high_strength_signals": high_strength_signals,
        }

    def average_signal_strength(self, signals: list[dict]) -> float:
        if not signals:
            return 0.0

        strengths = [
            signal.get("signal_strength", 0.0)
            for signal in signals
            if isinstance(signal.get("signal_strength", 0.0), (int, float))
        ]

        if not strengths:
            return 0.0

        return round(sum(strengths) / len(strengths), 4)

    def build_source_distribution(self, signals: list[dict]) -> dict:
        distribution = {}

        for signal in signals:
            source_system = signal.get("source_system") or "unknown"

            if source_system not in distribution:
                distribution[source_system] = 0

            distribution[source_system] += 1

        return dict(sorted(distribution.items()))

    def get_high_strength_signals(self, signals: list[dict]) -> list[dict]:
        high_strength_signals = []

        for signal in signals:
            signal_strength = signal.get("signal_strength", 0.0)

            if isinstance(signal_strength, (int, float)) and signal_strength >= 0.75:
                high_strength_signals.append(
                    {
                        "event_id": signal.get("event_id"),
                        "source_system": signal.get("source_system"),
                        "signal_type": signal.get("signal_type"),
                        "signal_strength": signal_strength,
                    }
                )

        return high_strength_signals

    def get_governance_posture(
        self,
        dominant_signal: str,
        average_signal_strength: float,
        high_strength_count: int,
        signal_counts: dict,
    ) -> str:
        if dominant_signal == "none":
            return "none"

        if signal_counts.get("evidence_conflict", 0) > 0:
            return "reconcile_evidence"

        if average_signal_strength >= 0.85 or high_strength_count >= 3:
            return "urgent_attention"

        if average_signal_strength >= 0.65 or high_strength_count >= 1:
            return "watch"

        if signal_counts.get("governance_unknown", 0) > 0:
            return "classification_gap"

        return "stable"