from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class SentinelOneConnector:
    source_system = "sentinelone"

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
                "threat_name": event.get("threatName"),
                "event_type": event.get("eventType"),
                "classification": event.get("classification"),
                "confidence_level": event.get("confidenceLevel"),
                "mitigation_status": event.get("mitigationStatus"),
                "analyst_verdict": event.get("analystVerdict"),
                "severity": event.get("severity"),
                "agent_name": event.get("agentName"),
                "site_name": event.get("siteName"),
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def get_event_id(self, event: dict) -> str:
        event_id = (
            event.get("id")
            or event.get("threatId")
            or event.get("activityUuid")
            or event.get("uuid")
            or "sentinelone-event-missing-id"
        )

        return str(event_id)

    def get_timestamp(self, event: dict) -> str:
        return (
            event.get("createdAt")
            or event.get("updatedAt")
            or event.get("detectedAt")
            or event.get("mitigatedAt")
            or "1970-01-01T00:00:00Z"
        )

    def map_event_type(self, event: dict) -> str:
        event_type = str(event.get("eventType", "")).lower()
        classification = str(event.get("classification", "")).lower()
        confidence_level = str(event.get("confidenceLevel", "")).lower()
        mitigation_status = str(event.get("mitigationStatus", "")).lower()
        analyst_verdict = str(event.get("analystVerdict", "")).lower()
        severity = str(event.get("severity", "")).lower()
        threat_name = str(event.get("threatName", "")).lower()

        # Confirmed malicious verdicts must always override clean/resolved status.
        if analyst_verdict in {"true_positive", "truepositive", "malicious"}:
            return "unauthorized_api_call"

        # Clean/healthy/resolved states should pass before generic severity/classification rules.
        if event_type in {
            "agent_online",
            "agent_connected",
            "agent_healthy",
            "agent_active",
            "threat_mitigated",
            "threat_resolved",
        }:
            return "verification_passed"

        if mitigation_status in {
            "mitigated",
            "remediated",
            "resolved",
            "marked_as_benign",
            "benign",
        }:
            return "verification_passed"

        if "agent online" in threat_name or "agent healthy" in threat_name:
            return "verification_passed"

        # Confirmed or likely malicious states.
        if classification in {
            "malware",
            "trojan",
            "ransomware",
            "exploit",
            "pua",
            "suspicious",
        }:
            return "unauthorized_api_call"

        if confidence_level in {"malicious", "suspicious"}:
            return "unauthorized_api_call"

        if severity in {"high", "critical"}:
            return "unauthorized_api_call"

        if "malware" in threat_name or "ransomware" in threat_name:
            return "unauthorized_api_call"

        if "agent offline" in threat_name or "sensor offline" in threat_name:
            return "environment_failure"

        return "security_review"