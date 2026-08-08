from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_port import (
    GovernanceInterventionActuationRequest,
)
from backend.app.gagf.governance_intervention_execution_result import (
    GovernanceInterventionExecutionDisposition,
)


GOVERNANCE_INTERVENTION_EXECUTION_ADAPTER_ID = (
    "governance-intervention-execution-adapter"
)
GOVERNANCE_INTERVENTION_EXECUTION_ADAPTER_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class GovernanceInterventionAdapterExecutionReport:
    """
    Raw report returned by a concrete intervention execution adapter.

    This is not a governed execution result, receipt, or verification record.
    The coordinator must validate and transform it into GEX-001F evidence.
    """

    disposition: GovernanceInterventionExecutionDisposition
    observations: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None


@runtime_checkable
class GovernanceInterventionExecutionAdapter(Protocol):
    """
    Narrow execution boundary for concrete intervention adapters.

    Implementations may perform the bounded external action authorized by the
    supplied contract. They must not issue governance authorization, create
    receipts, or independently claim outcome verification.
    """

    adapter_id: str
    adapter_version: str

    def execute(
        self,
        *,
        request: GovernanceInterventionActuationRequest,
        contract: GovernanceInterventionActuationContract,
        attempt_number: int,
    ) -> GovernanceInterventionAdapterExecutionReport:
        ...