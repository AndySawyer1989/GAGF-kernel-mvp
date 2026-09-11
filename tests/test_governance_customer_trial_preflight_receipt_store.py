import json
import sqlite3
from dataclasses import replace

import pytest

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
)
from backend.app.gagf.governance_customer_trial_preflight_decision import (
    build_customer_trial_preflight_decision,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    CustomerTrialPreflightReceiptStoreError,
    GovernanceCustomerTrialPreflightReceiptStore,
    TABLE_NAME,
)


EVALUATED_AT = "2026-09-10T21:45:00+00:00"


def build_package():
    return CustomerTrialEngagementPackage(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        client_display_name="Customer 001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        assessment_name=(
            "FIP Governance Assessment"
        ),
        period_start="2026-09-01",
        period_end="2026-09-30",
        workflows=(
            "Production change approval",
        ),
        organizational_units=(
            "Platform Engineering",
        ),
        objectives=(
            "Measure governance friction",
        ),
        expected_outcomes=(
            "Produce deterministic "
            "assessment findings",
        ),
        evidence_requirements=(
            CustomerTrialEvidenceRequirement(
                requirement_id="EVID-001",
                description=(
                    "Governed workflow evidence"
                ),
                minimum_records=30,
                accepted_formats=("csv",),
            ),
        ),
        data_classification="sanitized",
        prepared_by="FIP Trial Operator",
        customer_deliverables=(
            "Governance assessment report",
        ),
        trial_boundaries=(
            "Assessment ranking does not "
            "establish root cause.",
            "Recommendations do not authorize "
            "implementation.",
            "Assessment does not grant "
            "intervention authority.",
        ),
        completion_criteria=(
            "Governed report delivered",
            "Client receipt recorded",
            "Client response recorded",
            "Administrative closeout recorded",
        ),
    )


def build_decision(
    package=None,
):
    return (
        build_customer_trial_preflight_decision(
            package or build_package(),
            evaluated_at=EVALUATED_AT,
        )
    )


def test_persists_preflight_receipt(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    receipt = store.put(
        decision=build_decision()
    )

    assert receipt.hierarchy_key == (
        "tenant-alpha/"
        "client-customer-001/"
        "engagement-trial-001/"
        "assessment-trial-001"
    )

    assert len(
        receipt.decision_payload_hash
    ) == 64

    assert len(
        receipt.receipt_hash
    ) == 64


def test_receipt_binds_exact_decision_payload(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    decision = build_decision()

    receipt = store.put(
        decision=decision
    )

    expected_payload = json.loads(
        json.dumps(
            decision.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )

    assert (
        receipt.decision_payload
        == expected_payload
    )

    assert (
        receipt.decision_payload[
            "evaluated_at"
        ]
        == EVALUATED_AT
    )


def test_identical_persistence_is_idempotent(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    decision = build_decision()

    first = store.put(
        decision=decision
    )

    second = store.put(
        decision=decision
    )

    assert (
        second.receipt_hash
        == first.receipt_hash
    )

    assert second == first


def test_conflicting_decision_cannot_replace_receipt(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    store.put(
        decision=build_decision()
    )

    changed_package = replace(
        build_package(),
        period_start="2026-10-01",
        period_end="2026-09-30",
    )

    changed_decision = build_decision(
        changed_package
    )

    with pytest.raises(
        CustomerTrialPreflightReceiptStoreError,
        match=(
            "different governed decision material"
        ),
    ):
        store.put(
            decision=changed_decision
        )


def test_receipt_survives_store_restart(
    tmp_path,
):
    database_path = (
        tmp_path / "preflight.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            database_path
        )
    )

    first = first_store.put(
        decision=build_decision()
    )

    restarted_store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            database_path
        )
    )

    restored = restarted_store.get(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id=(
            "engagement-trial-001"
        ),
        assessment_id=(
            "assessment-trial-001"
        ),
    )

    assert restored is not None
    assert restored == first


def test_payload_tampering_is_detected(
    tmp_path,
):
    database_path = (
        tmp_path / "preflight.sqlite3"
    )

    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            database_path
        )
    )

    store.put(
        decision=build_decision()
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE {TABLE_NAME}
            SET decision_payload_json = ?
            """,
            (
                '{"tampered":true}',
            ),
        )

        connection.commit()

    with pytest.raises(
        CustomerTrialPreflightReceiptStoreError,
        match="payload hash",
    ):
        store.get(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id=(
                "engagement-trial-001"
            ),
            assessment_id=(
                "assessment-trial-001"
            ),
        )


def test_receipt_hash_tampering_is_detected(
    tmp_path,
):
    database_path = (
        tmp_path / "preflight.sqlite3"
    )

    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            database_path
        )
    )

    store.put(
        decision=build_decision()
    )

    with sqlite3.connect(
        database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE {TABLE_NAME}
            SET receipt_hash = ?
            """,
            (
                "0" * 64,
            ),
        )

        connection.commit()

    with pytest.raises(
        CustomerTrialPreflightReceiptStoreError,
        match="receipt hash",
    ):
        store.get(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id=(
                "engagement-trial-001"
            ),
            assessment_id=(
                "assessment-trial-001"
            ),
        )


def test_receipt_explicitly_preserves_authority_boundaries(
    tmp_path,
):
    store = (
        GovernanceCustomerTrialPreflightReceiptStore(
            tmp_path / "preflight.sqlite3"
        )
    )

    payload = store.put(
        decision=build_decision()
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "receipt_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_delivery_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_closeout_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )
