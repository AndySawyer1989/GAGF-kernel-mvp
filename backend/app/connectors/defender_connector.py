from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class DefenderConnector:
    source_system = "defender"

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_id = self.get_event_id(event)
        occurred_at = self.get_timestamp(event)

        return RawSecurityEvent(
            event_id=event_id,
            event_type=self.map_event_type(event),
            event_occurred_at=occurred_at,
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            kernel_eligible=True,
            source_system=self.source_system,
            metadata={
                "raw_payload": event,
                "title": event.get("title"),
                "severity": event.get("severity"),
                "category": event.get("category"),
                "status": event.get("status"),
                "classification": event.get("classification"),
                "determination": event.get("determination"),
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def get_event_id(self, event: dict) -> str:
        event_id = (
            event.get("id")
            or event.get("alertId")
            or event.get("incidentId")
            or event.get("incidentWebUrl")
            or "defender-event-missing-id"
        )

        return str(event_id)

    def get_timestamp(self, event: dict) -> str:
        return (
            event.get("createdDateTime")
            or event.get("lastUpdateDateTime")
            or event.get("resolvedDateTime")
            or "1970-01-01T00:00:00Z"
        )

    def map_event_type(self, event: dict) -> str:
        severity = str(event.get("severity", "")).lower()
        category = str(event.get("category", "")).lower()
        title = str(event.get("title", "")).lower()
        status = str(event.get("status", "")).lower()
        classification = str(event.get("classification", "")).lower()
        determination = str(event.get("determination", "")).lower()

        if classification == "truepositive":
            return "unauthorized_api_call"

        if determination in {
            "malware",
            "phishing",
            "credentialtheft",
            "apt",
            "securitypersonnel",
            "other",
        }:
            return "unauthorized_api_call"

        if severity in {"high", "critical"}:
            return "unauthorized_api_call"

        if "malware" in category or "malware" in title:
            return "unauthorized_api_call"

        if "credential" in category or "identity" in category:
            return "unauthorized_api_call"

        if status in {"resolved", "closed"}:
            return "verification_passed"

        if "endpoint" in category or "device" in category:
            return "environment_failure"

        return "security_review"