from backend.app.gagf.friction_signal_detection_service import (
    FrictionSignalDetectionService,
)
from backend.app.gagf.schemas import RawSecurityEvent, TimestampQuality


def make_event(
    event_id="evt-1",
    source_system="defender",
    event_type="unauthorized_api_call",
    metadata=None,
):
    if metadata is None:
        metadata = {}

    return RawSecurityEvent(
        event_id=event_id,
        event_type=event_type,
        event_occurred_at="2026-07-09T10:00:00Z",
        timestamp_quality=TimestampQuality.SOURCE_OCCURRED_AT,
        kernel_eligible=True,
        source_system=source_system,
        metadata=metadata,
    )


def test_friction_signal_detection_service_returns_empty_result():
    result = FrictionSignalDetectionService().detect_events([])

    assert result == {
        "status": "ok",
        "event_count": 0,
        "signal_count": 0,
        "friction_signal_count": 0,
        "dominant_friction_type": "none",
        "friction_posture": "none",
        "average_friction_intensity": 0.0,
        "friction_type_counts": {
            "evidence_friction": 0,
            "security_pressure": 0,
            "access_friction": 0,
            "process_friction": 0,
            "delivery_friction": 0,
            "operational_friction": 0,
        },
        "correlation_amplifier_count": 0,
        "correlation_amplifiers": [],
        "friction_signals": [],
    }


def test_friction_signal_detection_service_detects_security_pressure():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        )
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert result["status"] == "ok"
    assert result["event_count"] == 1
    assert result["signal_count"] == 1
    assert result["friction_signal_count"] == 1
    assert result["dominant_friction_type"] == "security_pressure"
    assert result["friction_posture"] == "severe_friction"
    assert result["average_friction_intensity"] == 0.88
    assert result["friction_type_counts"]["security_pressure"] == 1

    signal = result["friction_signals"][0]

    assert signal["event_id"] == "evt-1"
    assert signal["source_system"] == "defender"
    assert signal["source_signal_type"] == "security_risk"
    assert signal["friction_type"] == "security_pressure"
    assert signal["friction_intensity"] == 0.88
    assert signal["friction_band"] == "severe"
    assert "Security risk is creating governance pressure" in signal[
        "governance_interpretation"
    ]


def test_friction_signal_detection_service_detects_access_friction():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        )
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert result["dominant_friction_type"] == "access_friction"
    assert result["friction_posture"] == "high_friction"
    assert result["average_friction_intensity"] == 0.832

    signal = result["friction_signals"][0]

    assert signal["source_signal_type"] == "identity_friction"
    assert signal["friction_type"] == "access_friction"
    assert signal["friction_intensity"] == 0.832
    assert signal["friction_band"] == "high"


def test_friction_signal_detection_service_detects_process_and_delivery_friction():
    events = [
        make_event(
            event_id="evt-1",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
            },
        ),
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert result["event_count"] == 2
    assert result["signal_count"] == 2
    assert result["friction_signal_count"] == 2
    assert result["dominant_friction_type"] == "process_friction"
    assert result["friction_posture"] == "high_friction"
    assert result["average_friction_intensity"] == 0.685

    assert result["friction_type_counts"] == {
        "evidence_friction": 0,
        "security_pressure": 0,
        "access_friction": 0,
        "process_friction": 1,
        "delivery_friction": 1,
        "operational_friction": 0,
    }

    assert result["correlation_amplifier_count"] == 1
    assert result["correlation_amplifiers"][0]["relationship_type"] == (
        "process_delivery_coupling"
    )
    assert result["correlation_amplifiers"][0]["amplifier_strength"] == 0.73
    assert result["correlation_amplifiers"][0]["amplifier_band"] == "moderate"


def test_friction_signal_detection_service_detects_evidence_friction_as_severe():
    events = [
        make_event(
            event_id="evt-1",
            source_system="defender",
            event_type="security_resolution_mismatch",
            metadata={
                "status": "conflict",
                "severity": "high",
            },
        )
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert result["dominant_friction_type"] == "evidence_friction"
    assert result["friction_posture"] == "high_friction"
    assert result["average_friction_intensity"] == 0.81

    signal = result["friction_signals"][0]

    assert signal["source_signal_type"] == "evidence_conflict"
    assert signal["friction_type"] == "evidence_friction"
    assert signal["friction_intensity"] == 0.81
    assert signal["friction_band"] == "high"
    assert "Evidence disagreement" in signal["governance_interpretation"]


def test_friction_signal_detection_service_ignores_unknown_signals():
    events = [
        make_event(
            event_id="evt-1",
            source_system="unknown-source",
            event_type="unmapped_event",
        )
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert result["event_count"] == 1
    assert result["signal_count"] == 1
    assert result["friction_signal_count"] == 0
    assert result["dominant_friction_type"] == "none"
    assert result["friction_posture"] == "none"
    assert result["average_friction_intensity"] == 0.0
    assert result["friction_signals"] == []


def test_friction_signal_detection_service_detects_strong_correlation_amplifier():
    events = [
        make_event(
            event_id="evt-1",
            source_system="okta",
            event_type="login_failed",
            metadata={
                "outcome": "failed",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert result["friction_posture"] == "severe_friction"
    assert result["correlation_amplifier_count"] == 1

    amplifier = result["correlation_amplifiers"][0]

    assert amplifier["relationship_type"] == "access_security_coupling"
    assert amplifier["left_event_id"] == "evt-1"
    assert amplifier["right_event_id"] == "evt-2"
    assert amplifier["amplifier_strength"] == 0.91
    assert amplifier["amplifier_band"] == "strong"
    assert "amplify friction" in amplifier["governance_interpretation"]


def test_friction_signal_detection_service_sorts_friction_signals_by_intensity():
    events = [
        make_event(
            event_id="evt-1",
            source_system="github",
            event_type="pull_request_review_required",
            metadata={
                "state": "review_required",
            },
        ),
        make_event(
            event_id="evt-2",
            source_system="defender",
            event_type="unauthorized_api_call",
            metadata={
                "severity": "high",
                "status": "active",
            },
        ),
        make_event(
            event_id="evt-3",
            source_system="jira",
            event_type="approval_delayed",
            metadata={
                "status": "waiting",
            },
        ),
    ]

    result = FrictionSignalDetectionService().detect_events(events)

    assert [
        signal["friction_type"]
        for signal in result["friction_signals"]
    ] == [
        "security_pressure",
        "process_friction",
        "delivery_friction",
    ]


def test_friction_signal_detection_service_calculates_intensity_safely():
    service = FrictionSignalDetectionService()

    assert service.calculate_friction_intensity(
        base_intensity=0.80,
        signal_strength=1.0,
    ) == 0.88

    assert service.calculate_friction_intensity(
        base_intensity=0.80,
        signal_strength="unknown",
    ) == 0.48