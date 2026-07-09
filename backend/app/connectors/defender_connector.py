from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class DefenderConnector:
    """
    Converts Microsoft Defender-style endpoint/security evidence into
    GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-056.
    Later, it can be expanded to support Microsoft Defender for Endpoint,
    Defender XDR incidents, alerts, advanced hunting events, device risk,
    exposure signals, vulnerability findings, and investigation states.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_defender_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("id", "defender-event-missing-id"),
            event_type=event_type,
            source_system="defender",
            event_occurred_at=event.get("createdTime"),
            event_created_at=event.get("createdTime"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.90,
            cross_source_agreement=0.81,
            telemetry_completeness=0.88,
            kernel_eligible=True,
            metadata={
                "raw_payload": event,
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_defender_event_type(self, event: dict) -> str:
        title = event.get("title", "").lower()
        category = event.get("category", "").lower()
        severity = event.get("severity", "").lower()
        status = event.get("status", "").lower()
        classification = event.get("classification", "").lower()
        determination = event.get("determination", "").lower()
        alert_type = event.get("alertType", "").lower()

        if status in {"new", "inprogress", "in_progress", "active"}:
            if severity in {"high", "critical"}:
                return "unauthorized_api_call"

        if classification in {"truepositive", "true_positive"}:
            return "unauthorized_api_call"

        if determination in {"malware", "phishing", "compromisedaccount", "compromised_account"}:
            return "unauthorized_api_call"

        if severity in {"high", "critical"}:
            return "unauthorized_api_call"

        if "malware" in title or "ransomware" in title:
            return "unauthorized_api_call"

        if "suspicious" in title or "credential" in title:
            return "unauthorized_api_call"

        if "alert" in alert_type and status not in {"resolved", "closed"}:
            return "unauthorized_api_call"

        if status in {"resolved", "closed"}:
            return "verification_passed"

        if "device" in category and "healthy" in title:
            return "verification_passed"

        if title or category:
            return "historically_valid_control"

        return "historically_valid_control"