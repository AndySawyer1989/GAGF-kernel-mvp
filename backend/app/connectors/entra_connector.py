from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class EntraConnector:
    """
    Converts Microsoft Entra ID-style identity/security evidence into
    GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-050.
    Later, it can be expanded to support real Entra sign-in logs,
    audit logs, conditional access outcomes, risky users, risky sign-ins,
    MFA challenges, token events, and identity governance signals.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_entra_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("id", "entra-event-missing-id"),
            event_type=event_type,
            source_system="entra",
            event_occurred_at=event.get("createdDateTime"),
            event_created_at=event.get("createdDateTime"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.89,
            cross_source_agreement=0.79,
            telemetry_completeness=0.87,
            kernel_eligible=True,
            metadata={
                "raw_payload": event,
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_entra_event_type(self, event: dict) -> str:
        category = event.get("category", "").lower()
        activity = event.get("activityDisplayName", "").lower()
        status = event.get("status", {})
        failure_reason = status.get("failureReason", "").lower()
        result = status.get("errorCode")

        conditional_access_status = event.get("conditionalAccessStatus", "").lower()
        risk_state = event.get("riskState", "").lower()
        risk_level = event.get("riskLevelAggregated", "").lower()

        if result not in {None, 0, "0"}:
            return "failed_auth_burst"

        if "failure" in failure_reason:
            return "failed_auth_burst"

        if conditional_access_status in {"failure", "notapplied"}:
            return "unauthorized_api_call"

        if risk_state in {"atRisk", "confirmedCompromised"}:
            return "unauthorized_api_call"

        if risk_level in {"high", "medium"}:
            return "unauthorized_api_call"

        if "sign-in" in activity or "signin" in activity:
            return "verification_passed"

        if "usermanagement" in category or "user" in activity:
            return "historically_valid_control"

        return "historically_valid_control"