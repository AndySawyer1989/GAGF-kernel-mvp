from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


class OktaConnector:
    """
    Converts Okta-style identity/security evidence into GAGF RawSecurityEvent objects.

    This connector is intentionally small for US-047.
    Later, it can be expanded to support real Okta System Log events,
    authentication outcomes, MFA events, policy violations, suspicious activity,
    user lifecycle events, and risk signals.
    """

    def normalize_event(self, event: dict) -> RawSecurityEvent:
        event_type = self._map_okta_event_type(event)

        return RawSecurityEvent(
            event_id=event.get("uuid", "okta-event-missing-id"),
            event_type=event_type,
            source_system="okta",
            event_occurred_at=event.get("published"),
            event_created_at=event.get("published"),
            timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
            sensor_reliability=0.88,
            cross_source_agreement=0.78,
            telemetry_completeness=0.86,
            kernel_eligible=True,
            metadata={
                "raw_payload": event,
            },
        )

    def normalize_events(self, events: list[dict]) -> list[RawSecurityEvent]:
        return [self.normalize_event(event) for event in events]

    def _map_okta_event_type(self, event: dict) -> str:
        event_type = event.get("eventType", "").lower()
        outcome = event.get("outcome", {})
        outcome_result = outcome.get("result", "").lower()

        if "user.authentication.failed" in event_type:
            return "failed_auth_burst"

        if "user.mfa.attempt_bypass" in event_type:
            return "unauthorized_api_call"

        if "policy.mfa.attempt_bypass" in event_type:
            return "unauthorized_api_call"

        if "user.session.start" in event_type and outcome_result == "success":
            return "verification_passed"

        if "user.lifecycle" in event_type:
            return "historically_valid_control"

        if outcome_result == "failure":
            return "failed_auth_burst"

        return "historically_valid_control"