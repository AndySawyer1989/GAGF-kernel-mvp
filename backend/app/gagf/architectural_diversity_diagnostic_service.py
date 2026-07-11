class ArchitecturalDiversityDiagnosticService:
    component_type_priority = [
        "sequencer",
        "ledger",
        "kernel",
        "api",
        "worker",
        "graph",
        "connector",
        "unknown",
    ]

    criticality_weights = {
        "critical": 1.00,
        "high": 0.75,
        "medium": 0.50,
        "low": 0.25,
        "unknown": 0.25,
    }

    def diagnose_components(self, components: list[dict]) -> dict:
        normalized_components = [
            self.normalize_component(component)
            for component in components
        ]

        component_count = len(normalized_components)

        if component_count == 0:
            return self.empty_result()

        component_type_counts = self.count_values(
            normalized_components,
            "component_type",
        )
        subsystem_counts = self.count_values(
            normalized_components,
            "subsystem",
        )
        authority_zone_counts = self.count_values(
            normalized_components,
            "authority_zone",
        )
        redundancy_group_counts = self.count_values(
            normalized_components,
            "redundancy_group",
        )

        component_type_diversity = self.calculate_diversity_index(
            component_type_counts,
            component_count,
        )
        subsystem_diversity = self.calculate_diversity_index(
            subsystem_counts,
            component_count,
        )
        authority_zone_diversity = self.calculate_diversity_index(
            authority_zone_counts,
            component_count,
        )
        redundancy_diversity = self.calculate_diversity_index(
            redundancy_group_counts,
            component_count,
        )

        architectural_diversity_index = round(
            (
                component_type_diversity
                + subsystem_diversity
                + authority_zone_diversity
                + redundancy_diversity
            )
            / 4,
            4,
        )

        interface_balance_score = self.calculate_interface_balance(
            normalized_components
        )

        complexity_resilience_ratio = round(
            architectural_diversity_index * 0.60
            + redundancy_diversity * 0.25
            + interface_balance_score * 0.15,
            4,
        )

        mononal_risk_score = round(
            1.0 - architectural_diversity_index,
            4,
        )

        return {
            "status": "ok",
            "component_count": component_count,
            "architectural_diversity_index": architectural_diversity_index,
            "complexity_resilience_ratio": complexity_resilience_ratio,
            "mononal_risk_score": mononal_risk_score,
            "architecture_posture": self.get_architecture_posture(
                architectural_diversity_index,
                complexity_resilience_ratio,
            ),
            "concentration_risk": self.get_concentration_risk(
                mononal_risk_score
            ),
            "dominant_component_type": self.get_dominant_value(
                component_type_counts,
                self.component_type_priority,
            ),
            "component_type_counts": component_type_counts,
            "subsystem_counts": subsystem_counts,
            "authority_zone_counts": authority_zone_counts,
            "redundancy_group_counts": redundancy_group_counts,
            "diversity_breakdown": {
                "component_type_diversity": component_type_diversity,
                "subsystem_diversity": subsystem_diversity,
                "authority_zone_diversity": authority_zone_diversity,
                "redundancy_diversity": redundancy_diversity,
                "interface_balance_score": interface_balance_score,
            },
            "component_diagnostics": [
                self.build_component_diagnostic(component)
                for component in normalized_components
            ],
        }

    def empty_result(self) -> dict:
        return {
            "status": "ok",
            "component_count": 0,
            "architectural_diversity_index": 0.0,
            "complexity_resilience_ratio": 0.0,
            "mononal_risk_score": 0.0,
            "architecture_posture": "none",
            "concentration_risk": "none",
            "dominant_component_type": "none",
            "component_type_counts": {},
            "subsystem_counts": {},
            "authority_zone_counts": {},
            "redundancy_group_counts": {},
            "diversity_breakdown": {
                "component_type_diversity": 0.0,
                "subsystem_diversity": 0.0,
                "authority_zone_diversity": 0.0,
                "redundancy_diversity": 0.0,
                "interface_balance_score": 0.0,
            },
            "component_diagnostics": [],
        }

    def normalize_component(self, component: dict) -> dict:
        component_id = self.normalize_string(
            component.get("component_id")
            or component.get("id")
            or component.get("name")
            or "unknown"
        )

        component_type = self.normalize_string(
            component.get("component_type")
            or component.get("type")
            or "unknown"
        )

        subsystem = self.normalize_string(
            component.get("subsystem")
            or component.get("domain")
            or "unknown"
        )

        authority_zone = self.normalize_string(
            component.get("authority_zone")
            or component.get("decision_authority")
            or component.get("owner_zone")
            or "unknown"
        )

        redundancy_group = self.normalize_string(
            component.get("redundancy_group")
            or component.get("partition")
            or component_id
        )

        dependencies = self.normalize_collection(
            component.get("dependencies", [])
        )
        interfaces = self.normalize_collection(
            component.get("interfaces", [])
        )

        criticality = self.normalize_string(
            component.get("criticality") or "unknown"
        )

        if criticality not in self.criticality_weights:
            criticality = "unknown"

        return {
            "component_id": component_id,
            "component_type": component_type,
            "subsystem": subsystem,
            "authority_zone": authority_zone,
            "redundancy_group": redundancy_group,
            "dependencies": dependencies,
            "interfaces": interfaces,
            "criticality": criticality,
        }

    def build_component_diagnostic(self, component: dict) -> dict:
        dependency_count = len(component["dependencies"])
        interface_count = len(component["interfaces"])
        criticality_weight = self.criticality_weights[
            component["criticality"]
        ]

        local_complexity_score = round(
            min(
                1.0,
                dependency_count * 0.12
                + interface_count * 0.10
                + criticality_weight * 0.35,
            ),
            4,
        )

        return {
            "component_id": component["component_id"],
            "component_type": component["component_type"],
            "subsystem": component["subsystem"],
            "authority_zone": component["authority_zone"],
            "redundancy_group": component["redundancy_group"],
            "dependency_count": dependency_count,
            "interface_count": interface_count,
            "criticality": component["criticality"],
            "local_complexity_score": local_complexity_score,
        }

    def count_values(
        self,
        components: list[dict],
        field_name: str,
    ) -> dict:
        counts = {}

        for component in components:
            value = component[field_name]

            if value not in counts:
                counts[value] = 0

            counts[value] += 1

        return counts

    def calculate_diversity_index(
        self,
        counts: dict,
        component_count: int,
    ) -> float:
        if component_count <= 0:
            return 0.0

        return round(len(counts) / component_count, 4)

    def calculate_interface_balance(
        self,
        components: list[dict],
    ) -> float:
        if not components:
            return 0.0

        average_interface_count = sum(
            len(component["interfaces"])
            for component in components
        ) / len(components)

        return round(min(1.0, average_interface_count / 3), 4)

    def get_architecture_posture(
        self,
        architectural_diversity_index: float,
        complexity_resilience_ratio: float,
    ) -> str:
        if architectural_diversity_index <= 0.0:
            return "none"

        if (
            architectural_diversity_index >= 0.75
            and complexity_resilience_ratio >= 0.70
        ):
            return "adaptive_diverse_architecture"

        if (
            architectural_diversity_index >= 0.50
            and complexity_resilience_ratio >= 0.50
        ):
            return "mixed_resilience_architecture"

        if architectural_diversity_index >= 0.35:
            return "concentrated_architecture"

        return "mononal_architecture_risk"

    def get_concentration_risk(
        self,
        mononal_risk_score: float,
    ) -> str:
        if mononal_risk_score <= 0.0:
            return "none"

        if mononal_risk_score >= 0.75:
            return "critical"

        if mononal_risk_score >= 0.50:
            return "high"

        if mononal_risk_score >= 0.25:
            return "moderate"

        return "low"

    def get_dominant_value(
        self,
        counts: dict,
        priority_order: list[str],
    ) -> str:
        if not counts:
            return "none"

        max_count = max(counts.values())
        candidates = [
            value
            for value, count in counts.items()
            if count == max_count
        ]

        for value in priority_order:
            if value in candidates:
                return value

        return sorted(candidates)[0]

    def normalize_string(self, value) -> str:
        if value is None:
            return "unknown"

        normalized = str(value).strip().lower().replace(" ", "_")

        if not normalized:
            return "unknown"

        return normalized

    def normalize_collection(self, value) -> list:
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        if isinstance(value, set):
            return sorted(value)

        return [value]