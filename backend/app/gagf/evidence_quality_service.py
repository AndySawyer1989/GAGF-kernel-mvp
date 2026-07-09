from backend.app.gagf.source_registry import SourceRegistry


class EvidenceQualityService:
    weights = {
        "timestamp_quality": 0.25,
        "source_registered": 0.20,
        "source_enabled": 0.15,
        "metadata_completeness": 0.15,
        "kernel_role_present": 0.15,
        "trust_tier_weight": 0.10,
    }

    def score_event(self, event) -> dict:
        source_system = getattr(event, "source_system", None)
        source = SourceRegistry().get_source(source_system)

        factors = {
            "timestamp_quality": self.score_timestamp_quality(
                getattr(event, "timestamp_quality", None)
            ),
            "source_registered": 1.0 if source is not None else 0.0,
            "source_enabled": self.score_source_enabled(source),
            "metadata_completeness": self.score_metadata_completeness(
                getattr(event, "metadata", None)
            ),
            "kernel_role_present": self.score_kernel_role_present(source),
            "trust_tier_weight": self.score_trust_tier(source),
        }

        quality_score = self.calculate_weighted_score(factors)
        quality_band = self.get_quality_band(quality_score)

        return {
            "status": "ok",
            "event_id": getattr(event, "event_id", None),
            "source_system": source_system,
            "quality_score": quality_score,
            "quality_band": quality_band,
            "factors": factors,
        }

    def score_events(self, events: list) -> dict:
        scored_events = [self.score_event(event) for event in events]

        if not scored_events:
            average_quality_score = 0.0
        else:
            average_quality_score = round(
                sum(event["quality_score"] for event in scored_events)
                / len(scored_events),
                4,
            )

        return {
            "status": "ok",
            "event_count": len(scored_events),
            "average_quality_score": average_quality_score,
            "average_quality_band": self.get_quality_band(average_quality_score),
            "events": scored_events,
        }

    def score_timestamp_quality(self, timestamp_quality) -> float:
        value = self.normalize_value(timestamp_quality)

        if value == "SOURCE_OCCURRED_AT":
            return 1.0

        if value == "BACKFILLED_FROM_CREATED_AT":
            return 0.7

        if value == "MISSING_TIMESTAMP":
            return 0.0

        return 0.5

    def score_source_enabled(self, source: dict | None) -> float:
        if source is None:
            return 0.0

        return 1.0 if source.get("enabled") is True else 0.0

    def score_metadata_completeness(self, metadata) -> float:
        if not metadata:
            return 0.0

        if isinstance(metadata, dict) and metadata.get("raw_payload"):
            return 1.0

        if isinstance(metadata, dict):
            return 0.75

        return 0.25

    def score_kernel_role_present(self, source: dict | None) -> float:
        if source is None:
            return 0.0

        return 1.0 if source.get("kernel_role") else 0.0

    def score_trust_tier(self, source: dict | None) -> float:
        if source is None:
            return 0.0

        trust_tier = source.get("trust_tier")

        if trust_tier == "security":
            return 1.0

        if trust_tier == "operational":
            return 0.85

        return 0.5

    def calculate_weighted_score(self, factors: dict) -> float:
        score = 0.0

        for factor_name, factor_score in factors.items():
            score += factor_score * self.weights[factor_name]

        return round(score, 4)

    def get_quality_band(self, quality_score: float) -> str:
        if quality_score >= 0.85:
            return "high"

        if quality_score >= 0.60:
            return "medium"

        if quality_score > 0.0:
            return "low"

        return "invalid"

    def normalize_value(self, value) -> str:
        if value is None:
            return ""

        if hasattr(value, "value"):
            return str(value.value)

        return str(value)