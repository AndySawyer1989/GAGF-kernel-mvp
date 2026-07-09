from backend.app.gagf.source_registry import SourceRegistry


class CrossSourceAgreementService:
    expected_kernel_roles = {
        "identity_evidence",
        "threat_evidence",
        "delivery_evidence",
        "workflow_evidence",
        "incident_evidence",
    }

    def evaluate_agreement(self, events: list) -> dict:
        sources = self.get_unique_sources(events)
        kernel_roles = self.get_kernel_roles(events)
        event_types = self.get_event_types(events)
        missing_roles = self.get_missing_roles(kernel_roles)

        source_diversity_score = self.score_source_diversity(sources)
        kernel_role_coverage_score = self.score_kernel_role_coverage(kernel_roles)
        event_type_alignment_score = self.score_event_type_alignment(event_types)
        registered_source_score = self.score_registered_sources(sources)

        factors = {
            "source_diversity": source_diversity_score,
            "kernel_role_coverage": kernel_role_coverage_score,
            "event_type_alignment": event_type_alignment_score,
            "registered_sources": registered_source_score,
        }

        agreement_score = self.calculate_agreement_score(factors)
        agreement_band = self.get_agreement_band(agreement_score)

        return {
            "status": "ok",
            "event_count": len(events),
            "source_count": len(sources),
            "agreement_score": agreement_score,
            "agreement_band": agreement_band,
            "supporting_sources": sorted(sources),
            "kernel_roles_present": sorted(kernel_roles),
            "missing_roles": sorted(missing_roles),
            "event_types": sorted(event_types),
            "factors": factors,
        }

    def get_unique_sources(self, events: list) -> set[str]:
        sources = set()

        for event in events:
            source_system = getattr(event, "source_system", None)

            if source_system:
                sources.add(source_system)

        return sources

    def get_kernel_roles(self, events: list) -> set[str]:
        roles = set()
        registry = SourceRegistry()

        for event in events:
            source_system = getattr(event, "source_system", None)
            source = registry.get_source(source_system)

            if source and source.get("kernel_role"):
                roles.add(source["kernel_role"])

        return roles

    def get_event_types(self, events: list) -> set[str]:
        event_types = set()

        for event in events:
            event_type = getattr(event, "event_type", None)

            if event_type:
                event_types.add(str(event_type))

        return event_types

    def get_missing_roles(self, kernel_roles: set[str]) -> set[str]:
        return self.expected_kernel_roles - kernel_roles

    def score_source_diversity(self, sources: set[str]) -> float:
        source_count = len(sources)

        if source_count >= 3:
            return 1.0

        if source_count == 2:
            return 0.75

        if source_count == 1:
            return 0.4

        return 0.0

    def score_kernel_role_coverage(self, kernel_roles: set[str]) -> float:
        if not self.expected_kernel_roles:
            return 0.0

        return round(
            len(kernel_roles) / len(self.expected_kernel_roles),
            4,
        )

    def score_event_type_alignment(self, event_types: set[str]) -> float:
        event_type_count = len(event_types)

        if event_type_count == 0:
            return 0.0

        if event_type_count == 1:
            return 1.0

        if event_type_count == 2:
            return 0.75

        return 0.5

    def score_registered_sources(self, sources: set[str]) -> float:
        if not sources:
            return 0.0

        registry = SourceRegistry()
        registered_count = 0

        for source_system in sources:
            if registry.get_source(source_system) is not None:
                registered_count += 1

        return round(
            registered_count / len(sources),
            4,
        )

    def calculate_agreement_score(self, factors: dict) -> float:
        weights = {
            "source_diversity": 0.30,
            "kernel_role_coverage": 0.30,
            "event_type_alignment": 0.20,
            "registered_sources": 0.20,
        }

        score = 0.0

        for factor_name, factor_score in factors.items():
            score += factor_score * weights[factor_name]

        return round(score, 4)

    def get_agreement_band(self, agreement_score: float) -> str:
        if agreement_score >= 0.85:
            return "strong"

        if agreement_score >= 0.60:
            return "moderate"

        if agreement_score > 0.0:
            return "weak"

        return "none"