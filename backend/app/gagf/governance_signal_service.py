class GovernanceSignalService:
    signal_priority = [
        "evidence_conflict",
        "security_risk",
        "identity_friction",
        "workflow_friction",
        "delivery_friction",
        "operational_incident",
        "governance_unknown",
    ]

    def classify_events(self, events: list) -> dict:
        signal_records = [
            self.classify_event(event)
            for event in events
        ]

        signal_counts = self.build_signal_counts(signal_records)
        dominant_signal = self.get_dominant_signal(signal_counts)

        return {
            "status": "ok",
            "event_count": len(events),
            "signal_count": len(signal_records),
            "dominant_signal": dominant_signal,
            "signal_counts": signal_counts,
            "signals": signal_records,
        }

    def classify_event(self, event) -> dict:
        event_id = getattr(event, "event_id", None)
        source_system = self.normalize_text(getattr(event, "source_system", ""))
        event_type = self.normalize_text(getattr(event, "event_type", ""))
        metadata = self.get_metadata(event)

        signal_type = self.detect_signal_type(
            source_system=source_system,
            event_type=event_type,
            metadata=metadata,
        )

        return {
            "event_id": event_id,
            "source_system": source_system,
            "event_type": event_type,
            "signal_type": signal_type,
            "signal_strength": self.get_signal_strength(signal_type, metadata),
            "governance_interpretation": self.get_governance_interpretation(
                signal_type
            ),
        }

    def detect_signal_type(
        self,
        source_system: str,
        event_type: str,
        metadata: dict,
    ) -> str:
        text = self.combined_text(
            source_system=source_system,
            event_type=event_type,
            metadata=metadata,
        )

        if self.contains_any(
            text,
            {
                "conflict",
                "mismatch",
                "contradiction",
                "inconsistent",
                "disagreement",
            },
        ):
            return "evidence_conflict"

        if source_system in {"defender", "sentinelone"}:
            return "security_risk"

        if self.contains_any(
            text,
            {
                "malware",
                "ransomware",
                "threat",
                "unauthorized_api_call",
                "vulnerability",
                "critical",
                "high",
                "malicious",
                "active",
            },
        ):
            return "security_risk"

        if source_system in {"okta", "entra"}:
            return "identity_friction"

        if self.contains_any(
            text,
            {
                "mfa",
                "login_failed",
                "sign_in_failed",
                "authentication_failed",
                "access_denied",
                "conditional_access",
                "identity",
                "access",
            },
        ):
            return "identity_friction"

        if source_system in {"jira"}:
            return "workflow_friction"

        if self.contains_any(
            text,
            {
                "approval_required",
                "approval_delayed",
                "work_blocked",
                "blocked",
                "dependency_wait",
                "waiting",
                "stalled",
                "ownership_gap",
            },
        ):
            return "workflow_friction"

        if source_system in {"github"}:
            return "delivery_friction"

        if self.contains_any(
            text,
            {
                "pull_request",
                "merge",
                "build_failed",
                "deployment_failed",
                "ci_failed",
                "review_required",
                "branch_protection",
            },
        ):
            return "delivery_friction"

        if source_system in {"servicenow"}:
            return "operational_incident"

        if self.contains_any(
            text,
            {
                "incident",
                "service_request",
                "change_request",
                "outage",
                "environment_failure",
                "service_degradation",
            },
        ):
            return "operational_incident"

        return "governance_unknown"

    def get_signal_strength(self, signal_type: str, metadata: dict) -> float:
        text = self.combined_text(
            source_system="",
            event_type="",
            metadata=metadata,
        )

        if signal_type == "governance_unknown":
            return 0.0

        if self.contains_any(
            text,
            {
                "critical",
                "severe",
                "ransomware",
                "outage",
                "blocked",
                "active",
                "failed",
            },
        ):
            return 1.0

        if self.contains_any(
            text,
            {
                "high",
                "warning",
                "delayed",
                "waiting",
                "degraded",
            },
        ):
            return 0.75

        return 0.5

    def get_governance_interpretation(self, signal_type: str) -> str:
        interpretations = {
            "evidence_conflict": (
                "Evidence sources are producing inconsistent claims and should "
                "be reconciled before confidence increases."
            ),
            "security_risk": (
                "Security telemetry indicates possible risk requiring governance "
                "attention."
            ),
            "identity_friction": (
                "Identity or access telemetry indicates authentication, authorization, "
                "or policy friction."
            ),
            "workflow_friction": (
                "Work management telemetry indicates process delay, blockage, "
                "dependency wait, or ownership friction."
            ),
            "delivery_friction": (
                "Delivery telemetry indicates development, merge, build, review, "
                "or deployment friction."
            ),
            "operational_incident": (
                "Operational telemetry indicates incident, service, change, or "
                "environment instability."
            ),
            "governance_unknown": (
                "The event does not yet map to a known governance signal."
            ),
        }

        return interpretations.get(
            signal_type,
            interpretations["governance_unknown"],
        )

    def build_signal_counts(self, signal_records: list[dict]) -> dict:
        counts = {
            "evidence_conflict": 0,
            "security_risk": 0,
            "identity_friction": 0,
            "workflow_friction": 0,
            "delivery_friction": 0,
            "operational_incident": 0,
            "governance_unknown": 0,
        }

        for record in signal_records:
            signal_type = record.get("signal_type", "governance_unknown")

            if signal_type not in counts:
                counts[signal_type] = 0

            counts[signal_type] += 1

        return counts

    def get_dominant_signal(self, signal_counts: dict) -> str:
        if not signal_counts or sum(signal_counts.values()) == 0:
            return "none"

        max_count = max(signal_counts.values())

        candidates = [
            signal
            for signal, count in signal_counts.items()
            if count == max_count
        ]

        for signal in self.signal_priority:
            if signal in candidates:
                return signal

        return sorted(candidates)[0]

    def combined_text(
        self,
        source_system: str,
        event_type: str,
        metadata: dict,
    ) -> str:
        values = [
            source_system,
            event_type,
        ]

        if isinstance(metadata, dict):
            values.extend(
                str(value)
                for value in metadata.values()
                if value is not None
            )

        return " ".join(values).lower()

    def contains_any(self, text: str, terms: set[str]) -> bool:
        return any(term in text for term in terms)

    def get_metadata(self, event) -> dict:
        metadata = getattr(event, "metadata", {}) or {}

        if isinstance(metadata, dict):
            return metadata

        return {}

    def normalize_text(self, value) -> str:
        if value is None:
            return ""

        if hasattr(value, "value"):
            return str(value.value).lower()

        return str(value).lower()