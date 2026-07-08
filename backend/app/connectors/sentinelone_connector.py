from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class SentinelOneConnector:
    """
    Converts SentinelOne-style endpoint/security evidence into
    GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-053.
    Later, it can be expanded to support real SentinelOne threats,
    alerts, agents, mitigation states, STAR rules, Deep Visibility events,
    malware detections, suspicious processes, and endpoint isolation events.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_sentinelone_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("id", "sentinelone-event-missing-id"),
            event_type=event_type,
            source_system="sentinelone",
            event_occurred_at=event.get("createdAt"),
            event_created_at=event.get("createdAt"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.91,
            cross_source_agreement=0.80,
            telemetry_completeness=0.88,
            kernel_eligible=True,
            metadata={
                "raw_payload": event,
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_sentinelone_event_type(self, event: dict) -> str:
        threat_name = event.get("threatName", "").lower()
        classification = event.get("classification", "").lower()
        confidence_level = event.get("confidenceLevel", "").lower()
        mitigation_status = event.get("mitigationStatus", "").lower()
        incident_status = event.get("incidentStatus", "").lower()
        analyst_verdict = event.get("analystVerdict", "").lower()
        event_type = event.get("eventType", "").lower()

        if mitigation_status in {"not_mitigated", "unresolved", "active"}:
            return "unauthorized_api_call"

        if incident_status in {"unresolved", "in_progress"}:
            return "unauthorized_api_call"

        if analyst_verdict in {"true_positive", "suspicious"}:
            return "unauthorized_api_call"

        if "agent" in event_type and "online" in event_type:
            return "verification_passed"

        if mitigation_status in {"mitigated", "resolved"}:
            return "verification_passed"

        if incident_status == "resolved":
            return "verification_passed"

        if confidence_level in {"malicious", "high"}:
            return "unauthorized_api_call"

        if "malware" in classification or "ransomware" in classification:
            return "unauthorized_api_call"

        if "threat" in event_type or "detection" in event_type:
            return "unauthorized_api_call"

        if threat_name:
            return "historically_valid_control"

        return "historically_valid_control"