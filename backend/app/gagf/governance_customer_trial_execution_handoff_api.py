from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from pydantic import (
    BaseModel,
    Field,
)

from backend.app.gagf.governance_commercial_paid_assessment_adapter import (
    CommercialContractExecutionEventInput,
    CommercialPaidAssessmentAdapterError,
    CommercialPaidWorkAuthorizationInput,
    GovernanceCommercialPaidAssessmentAdapter,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    CommercialPaidAssessmentExecutionInputBindingError,
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceiptConflictError,
    CustomerTrialExecutionHandoffReceiptIntegrityError,
    CustomerTrialExecutionHandoffReceiptStoreError,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_service import (
    GovernanceCustomerTrialExecutionHandoffService,
)


CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_TAG = (
    "governance-customer-trial-execution-handoff"
)


def _error_detail(
    *,
    code: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
    }


class CustomerTrialContractExecutionRequest(
    BaseModel
):
    contract_execution_event_id: str = Field(
        min_length=1
    )

    contract_executed: bool

    contract_execution_review_ready: bool

    contract_execution_confirmed: bool

    executed_contract_reference_recorded: bool

    executed_at_recorded: bool

    all_required_signatures_recorded: bool

    human_operator_confirmed_execution: bool

    requires_final_paid_work_authorization: bool

    human_boundary_required: bool

    gagf_kernel_authoritative: bool

    ai_override_allowed: bool

    def to_domain(
        self,
    ) -> CommercialContractExecutionEventInput:
        return CommercialContractExecutionEventInput(
            contract_execution_event_id=(
                self.contract_execution_event_id
            ),
            contract_executed=(
                self.contract_executed
            ),
            contract_execution_review_ready=(
                self.contract_execution_review_ready
            ),
            contract_execution_confirmed=(
                self.contract_execution_confirmed
            ),
            executed_contract_reference_recorded=(
                self.executed_contract_reference_recorded
            ),
            executed_at_recorded=(
                self.executed_at_recorded
            ),
            all_required_signatures_recorded=(
                self.all_required_signatures_recorded
            ),
            human_operator_confirmed_execution=(
                self.human_operator_confirmed_execution
            ),
            requires_final_paid_work_authorization=(
                self.requires_final_paid_work_authorization
            ),
            human_boundary_required=(
                self.human_boundary_required
            ),
            gagf_kernel_authoritative=(
                self.gagf_kernel_authoritative
            ),
            ai_override_allowed=(
                self.ai_override_allowed
            ),
        )


class CustomerTrialPaidWorkAuthorizationRequest(
    BaseModel
):
    authorization_id: str = Field(
        min_length=1
    )

    tenant_id: str = Field(
        min_length=1
    )

    client_id: str = Field(
        min_length=1
    )

    engagement_id: str = Field(
        min_length=1
    )

    assessment_id: str = Field(
        min_length=1
    )

    contract_execution_event_id: str = Field(
        min_length=1
    )

    authorized_by: str = Field(
        min_length=1
    )

    authorized_at: str = Field(
        min_length=1
    )

    paid_assessment_authorized: bool

    def to_domain(
        self,
    ) -> CommercialPaidWorkAuthorizationInput:
        return CommercialPaidWorkAuthorizationInput(
            authorization_id=(
                self.authorization_id
            ),
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
            contract_execution_event_id=(
                self.contract_execution_event_id
            ),
            authorized_by=(
                self.authorized_by
            ),
            authorized_at=(
                self.authorized_at
            ),
            paid_assessment_authorized=(
                self.paid_assessment_authorized
            ),
        )


class CustomerTrialExecutionHandoffApiRequest(
    BaseModel
):
    tenant_id: str = Field(
        min_length=1
    )

    client_id: str = Field(
        min_length=1
    )

    engagement_id: str = Field(
        min_length=1
    )

    assessment_id: str = Field(
        min_length=1
    )

    execution_input_binding_hash: str = Field(
        min_length=64,
        max_length=64,
    )

    contract_execution_event: (
        CustomerTrialContractExecutionRequest
    )

    paid_work_authorization: (
        CustomerTrialPaidWorkAuthorizationRequest
    )

    @property
    def hierarchy_key(
        self,
    ) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )


def create_customer_trial_execution_handoff_router(
    *,
    service:
        GovernanceCustomerTrialExecutionHandoffService,
    execution_input_binding_service:
        GovernanceCommercialPaidAssessmentExecutionInputBindingService,
    adapter:
        GovernanceCommercialPaidAssessmentAdapter
        | None = None,
) -> APIRouter:
    """
    Expose the controlled customer-trial
    execution-handoff boundary.

    This API may:
    - restore an immutable execution-input binding,
    - reconstruct the governed execution request,
    - validate existing contract execution evidence,
    - validate existing paid-work authorization,
    - prepare the existing paid execution handoff,
    - persist the customer-trial handoff audit receipt.

    It does not:
    - execute an assessment,
    - establish contract execution by itself,
    - create paid-work authorization,
    - approve recovery,
    - approve delivery,
    - record delivery,
    - establish intervention authority.
    """

    effective_adapter = (
        adapter
        if adapter is not None
        else GovernanceCommercialPaidAssessmentAdapter()
    )

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_TAG
        ],
    )

    @router.post(
        "/execution-handoff",
        status_code=status.HTTP_201_CREATED,
    )
    def prepare_execution_handoff(
        request:
            CustomerTrialExecutionHandoffApiRequest,
    ) -> dict[str, Any]:
        try:
            binding = (
                execution_input_binding_service.get(
                    hierarchy_key=(
                        request.hierarchy_key
                    )
                )
            )

            if (
                binding.binding_hash
                != request.execution_input_binding_hash
            ):
                raise (
                    CommercialPaidAssessmentExecutionInputBindingError(
                        "execution-input binding hash "
                        "does not match stored immutable binding"
                    )
                )

            assessment_execution_request = (
                execution_input_binding_service
                .reconstruct_request(
                    binding=binding
                )
            )

            if (
                assessment_execution_request
                .context
                .hierarchy_key
                != request.hierarchy_key
            ):
                raise (
                    CommercialPaidAssessmentExecutionInputBindingError(
                        "reconstructed execution request "
                        "hierarchy mismatch"
                    )
                )

            contract_execution_event = (
                effective_adapter
                .build_contract_execution_event(
                    payload=(
                        request
                        .contract_execution_event
                        .to_domain()
                    )
                )
            )

            paid_work_authorization = (
                effective_adapter
                .build_paid_work_authorization(
                    payload=(
                        request
                        .paid_work_authorization
                        .to_domain()
                    )
                )
            )

            result = service.prepare(
                tenant_id=request.tenant_id,
                client_id=request.client_id,
                engagement_id=(
                    request.engagement_id
                ),
                assessment_id=(
                    request.assessment_id
                ),
                contract_execution_event=(
                    contract_execution_event
                ),
                paid_work_authorization=(
                    paid_work_authorization
                ),
                assessment_execution_request=(
                    assessment_execution_request
                ),
            )

            return {
                "status": "ok",
                "api_version": (
                    CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_VERSION
                ),
                "authority": "HANDOFF_PREPARATION_ONLY",
                "execution_input_binding": {
                    "hierarchy_key":
                        binding.hierarchy_key,
                    "binding_hash":
                        binding.binding_hash,
                    "assessment_execution_request_hash": (
                        binding
                        .assessment_execution_request_hash
                    ),
                },
                "result":
                    result.to_dict(),
                "boundaries": {
                    "api_does_not_execute_assessment":
                        True,
                    "api_does_not_create_paid_work_authority":
                        True,
                    "api_does_not_create_contract_authority":
                        True,
                    "api_does_not_authorize_recovery":
                        True,
                    "api_does_not_authorize_delivery":
                        True,
                    "api_does_not_authorize_intervention":
                        True,
                    (
                        "existing_paid_execution_handoff_"
                        "remains_authoritative"
                    ):
                        True,
                },
            }

        except (
            CommercialPaidAssessmentAdapterError,
            CommercialPaidAssessmentExecutionInputBindingError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "EXECUTION_HANDOFF_VALIDATION_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

        except (
            CustomerTrialExecutionHandoffReceiptConflictError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "EXECUTION_HANDOFF_RECEIPT_CONFLICT"
                    ),
                    message=str(exc),
                ),
            ) from exc

        except (
            CustomerTrialExecutionHandoffReceiptIntegrityError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "EXECUTION_HANDOFF_INTEGRITY_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

        except (
            CustomerTrialExecutionHandoffReceiptStoreError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "EXECUTION_HANDOFF_STORE_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "execution-handoff-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_execution_handoff_status(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        try:
            result = service.status(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )

            return {
                "status": "ok",
                "api_version": (
                    CUSTOMER_TRIAL_EXECUTION_HANDOFF_API_VERSION
                ),
                "authority": "READ_ONLY",
                "result":
                    result.to_dict(),
                "boundaries": {
                    "status_is_read_only":
                        True,
                    "status_is_not_execution_authority":
                        True,
                    "status_is_not_recovery_authority":
                        True,
                    "status_is_not_delivery_authority":
                        True,
                    "status_is_not_closeout_authority":
                        True,
                    "status_is_not_intervention_authority":
                        True,
                },
            }

        except (
            CustomerTrialExecutionHandoffReceiptStoreError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "EXECUTION_HANDOFF_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router