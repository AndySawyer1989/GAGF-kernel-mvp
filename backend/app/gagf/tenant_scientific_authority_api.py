from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_authorization import (
    ScientificAuthorityAction,
    ScientificAuthorityAuthorizationPolicy,
    ScientificAuthorizationRequest,
    ScientificTrustSignals,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    get_calculation_contract,
)
from backend.app.gagf.scientific_evidence_checkpoint_replay_verifier import (
    ScientificEvidenceCheckpointReplayVerifier,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificContextBindingConflictError,
    ScientificContextBindingLedger,
    ScientificExecutionContext,
    ScientificExecutionContextBindingBuilder,
    ScientificExecutionContextError,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    ScientificPipelineRecoveryCoordinator,
)
from backend.app.gagf.tenant_artifact_collision_guard import (
    CrossTenantArtifactCollisionError,
    TenantArtifactCollisionGuard,
)
from backend.app.gagf.tenant_scientific_artifact_access import (
    TenantScientificArtifactAccessDeniedError,
    TenantScientificArtifactAccessService,
    TenantScientificArtifactBindingConflictError,
    TenantScientificArtifactNotFoundError,
    TenantScientificArtifactUnboundError,
)


TENANT_SCIENTIFIC_AUTHORITY_API_ID = (
    "tenant-scientific-authority-api"
)
TENANT_SCIENTIFIC_AUTHORITY_API_VERSION = "0.2.0"


@dataclass(frozen=True, slots=True)
class TenantScientificAuthorityApiPaths:
    authority_database_path: Path
    audit_database_path: Path
    checkpoint_database_path: Path
    journal_database_path: Path
    context_binding_database_path: Path


class TenantAuthorityEvidenceRequest(BaseModel):
    deterministic_replay_verified: bool
    canonical_input_binding_verified: bool
    calculation_version_frozen: bool
    regression_suite_passed: bool
    validation_report_present: bool
    constitutional_approval_present: bool

    def to_domain(self) -> AuthorityEscalationEvidence:
        return AuthorityEscalationEvidence(
            deterministic_replay_verified=(
                self.deterministic_replay_verified
            ),
            canonical_input_binding_verified=(
                self.canonical_input_binding_verified
            ),
            calculation_version_frozen=(
                self.calculation_version_frozen
            ),
            regression_suite_passed=(
                self.regression_suite_passed
            ),
            validation_report_present=(
                self.validation_report_present
            ),
            constitutional_approval_present=(
                self.constitutional_approval_present
            ),
        )


class TenantTrustSignalsRequest(BaseModel):
    credential_verified: bool
    session_verified: bool
    device_trusted: bool
    step_up_verified: bool = False
    tenant_membership_verified: bool

    def to_domain(self) -> ScientificTrustSignals:
        return ScientificTrustSignals(
            credential_verified=self.credential_verified,
            session_verified=self.session_verified,
            device_trusted=self.device_trusted,
            step_up_verified=self.step_up_verified,
            tenant_membership_verified=(
                self.tenant_membership_verified
            ),
        )


class TenantScientificAuthorityEvaluationRequest(BaseModel):
    calculation_id: str
    requested_authority: CalculationAuthority
    constitutional_approval_submitted: bool = False
    evidence: TenantAuthorityEvidenceRequest
    trust_signals: TenantTrustSignalsRequest


def create_tenant_scientific_authority_router(
    *,
    paths: TenantScientificAuthorityApiPaths,
) -> APIRouter:
    router = APIRouter(
        prefix="/tenant-scientific-authority",
        tags=["tenant-scientific-authority"],
    )

    coordinator = ScientificPipelineRecoveryCoordinator(
        authority_database_path=paths.authority_database_path,
        audit_database_path=paths.audit_database_path,
        checkpoint_database_path=paths.checkpoint_database_path,
        journal_database_path=paths.journal_database_path,
    )

    binding_ledger = ScientificContextBindingLedger(
        paths.context_binding_database_path
    )

    authorization_policy = (
        ScientificAuthorityAuthorizationPolicy()
    )

    artifact_access = TenantScientificArtifactAccessService(
        authority_database_path=paths.authority_database_path,
        checkpoint_database_path=paths.checkpoint_database_path,
        journal_database_path=paths.journal_database_path,
        context_binding_database_path=(
            paths.context_binding_database_path
        ),
    )

    collision_guard = TenantArtifactCollisionGuard(
        paths.context_binding_database_path
    )

    def build_context(
        *,
        tenant_id: str,
        actor_id: str,
        credential_id: str,
        session_id: str,
        role_id: str,
        policy_scope: str,
        request_id: str,
        correlation_id: str,
    ) -> ScientificExecutionContext:
        try:
            return ScientificExecutionContext(
                tenant_id=tenant_id,
                actor_id=actor_id,
                credential_id=credential_id,
                session_id=session_id,
                role_id=role_id,
                policy_scope=policy_scope,
                request_id=request_id,
                correlation_id=correlation_id,
            )
        except ScientificExecutionContextError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    def build_trust_signals(
        *,
        credential_verified: bool,
        session_verified: bool,
        device_trusted: bool,
        tenant_membership_verified: bool,
        step_up_verified: bool = False,
    ) -> ScientificTrustSignals:
        return ScientificTrustSignals(
            credential_verified=credential_verified,
            session_verified=session_verified,
            device_trusted=device_trusted,
            step_up_verified=step_up_verified,
            tenant_membership_verified=(
                tenant_membership_verified
            ),
        )

    def authorize(
        *,
        context: ScientificExecutionContext,
        action: ScientificAuthorityAction,
        target_tenant_id: str,
        trust_signals: ScientificTrustSignals,
        requested_authority: CalculationAuthority | None = None,
        constitutional_approval_submitted: bool = False,
    ) -> dict:
        authorization_request = ScientificAuthorizationRequest(
            context=context,
            action=action,
            target_tenant_id=target_tenant_id,
            requested_authority=requested_authority,
            constitutional_approval_submitted=(
                constitutional_approval_submitted
            ),
            trust_signals=trust_signals,
        )

        decision, receipt = (
            authorization_policy.evaluate_with_receipt(
                authorization_request
            )
        )

        if not decision.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": (
                        "Scientific authority request was denied."
                    ),
                    "decision": decision.to_dict(),
                    "authorization_receipt": receipt.to_dict(),
                },
            )

        return {
            "decision": decision.to_dict(),
            "receipt": receipt.to_dict(),
        }

    def handle_artifact_error(
        exc: Exception,
    ) -> None:
        if isinstance(
            exc,
            TenantScientificArtifactNotFoundError,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        if isinstance(
            exc,
            (
                TenantScientificArtifactAccessDeniedError,
                TenantScientificArtifactUnboundError,
            ),
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc

        if isinstance(
            exc,
            TenantScientificArtifactBindingConflictError,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        raise exc

    @router.post(
        "/evaluate",
        status_code=status.HTTP_200_OK,
    )
    def evaluate(
        request: TenantScientificAuthorityEvaluationRequest,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_target_tenant_id: str = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.EVALUATE,
            target_tenant_id=x_target_tenant_id,
            requested_authority=request.requested_authority,
            constitutional_approval_submitted=(
                request.constitutional_approval_submitted
            ),
            trust_signals=request.trust_signals.to_domain(),
        )

        try:
            contract = get_calculation_contract(
                request.calculation_id
            )
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Scientific calculation contract was not found."
                ),
            ) from exc

        try:
            pipeline_result = coordinator.execute(
                contract=contract,
                requested_authority=request.requested_authority,
                evidence=request.evidence.to_domain(),
            )

            binding = (
                ScientificExecutionContextBindingBuilder()
                .build(
                    context=context,
                    result=pipeline_result,
                )
            )

            collision_decision = collision_guard.enforce(
                binding
            )

            binding_record = binding_ledger.append(
                binding
            )

        except CrossTenantArtifactCollisionError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        except ScientificContextBindingConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Tenant-bound scientific authority "
                    "execution failed: "
                    + str(exc)
                ),
            ) from exc

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            "execution": pipeline_result.to_dict(),
            "artifact_collision_guard": (
                collision_decision.to_dict()
            ),
            "context_binding": binding_record.to_dict(),
        }

    @router.get("/receipts/{receipt_hash}")
    def get_receipt(
        receipt_hash: str,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_credential_verified: bool = Header(...),
        x_session_verified: bool = Header(...),
        x_device_trusted: bool = Header(...),
        x_tenant_membership_verified: bool = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.READ_RECEIPT,
            target_tenant_id=x_tenant_id,
            trust_signals=build_trust_signals(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        try:
            access = artifact_access.get_authority_receipt(
                tenant_id=x_tenant_id,
                receipt_hash=receipt_hash,
            )
        except Exception as exc:
            handle_artifact_error(exc)
            raise

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            **access.to_dict(),
        }

    @router.get("/checkpoints/{checkpoint_hash}")
    def get_checkpoint(
        checkpoint_hash: str,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_credential_verified: bool = Header(...),
        x_session_verified: bool = Header(...),
        x_device_trusted: bool = Header(...),
        x_tenant_membership_verified: bool = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.READ_CHECKPOINT,
            target_tenant_id=x_tenant_id,
            trust_signals=build_trust_signals(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        try:
            access = artifact_access.get_checkpoint(
                tenant_id=x_tenant_id,
                checkpoint_hash=checkpoint_hash,
            )
        except Exception as exc:
            handle_artifact_error(exc)
            raise

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            **access.to_dict(),
        }

    @router.post(
        "/checkpoints/{checkpoint_hash}/verify"
    )
    def verify_checkpoint(
        checkpoint_hash: str,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_credential_verified: bool = Header(...),
        x_session_verified: bool = Header(...),
        x_device_trusted: bool = Header(...),
        x_tenant_membership_verified: bool = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.VERIFY_CHECKPOINT,
            target_tenant_id=x_tenant_id,
            trust_signals=build_trust_signals(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        try:
            access = artifact_access.get_checkpoint(
                tenant_id=x_tenant_id,
                checkpoint_hash=checkpoint_hash,
            )
        except Exception as exc:
            handle_artifact_error(exc)
            raise

        checkpoint_record = (
            artifact_access.checkpoint_ledger.get_by_hash(
                checkpoint_hash
            )
        )

        if checkpoint_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Scientific evidence checkpoint was not found."
                ),
            )

        verification = (
            ScientificEvidenceCheckpointReplayVerifier()
            .verify(
                checkpoint=checkpoint_record.checkpoint,
                authority_database_path=(
                    paths.authority_database_path
                ),
                audit_database_path=(
                    paths.audit_database_path
                ),
            )
        )

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            "binding_hash": access.binding_hash,
            "verification": verification.to_dict(),
        }

    @router.get("/executions/{execution_id}")
    def get_execution(
        execution_id: str,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_credential_verified: bool = Header(...),
        x_session_verified: bool = Header(...),
        x_device_trusted: bool = Header(...),
        x_tenant_membership_verified: bool = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.READ_EXECUTION,
            target_tenant_id=x_tenant_id,
            trust_signals=build_trust_signals(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        try:
            access = artifact_access.get_execution(
                tenant_id=x_tenant_id,
                execution_id=execution_id,
            )
        except Exception as exc:
            handle_artifact_error(exc)
            raise

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            **access.to_dict(),
        }

    @router.get("/bindings/{binding_hash}")
    def get_binding(
        binding_hash: str,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_credential_verified: bool = Header(...),
        x_session_verified: bool = Header(...),
        x_device_trusted: bool = Header(...),
        x_tenant_membership_verified: bool = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.READ_EXECUTION,
            target_tenant_id=x_tenant_id,
            trust_signals=build_trust_signals(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        try:
            access = artifact_access.get_context_binding(
                tenant_id=x_tenant_id,
                binding_hash=binding_hash,
            )
        except Exception as exc:
            handle_artifact_error(exc)
            raise

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            **access.to_dict(),
        }

    @router.get("/tenants/{tenant_id}/bindings")
    def list_tenant_bindings(
        tenant_id: str,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
        x_credential_verified: bool = Header(...),
        x_session_verified: bool = Header(...),
        x_device_trusted: bool = Header(...),
        x_tenant_membership_verified: bool = Header(...),
    ) -> dict:
        context = build_context(
            tenant_id=x_tenant_id,
            actor_id=x_actor_id,
            credential_id=x_credential_id,
            session_id=x_session_id,
            role_id=x_role_id,
            policy_scope=x_policy_scope,
            request_id=x_request_id,
            correlation_id=x_correlation_id,
        )

        authorization = authorize(
            context=context,
            action=ScientificAuthorityAction.READ_EXECUTION,
            target_tenant_id=tenant_id,
            trust_signals=build_trust_signals(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        records = artifact_access.list_tenant_bindings(
            tenant_id=tenant_id
        )

        return {
            "api_id": TENANT_SCIENTIFIC_AUTHORITY_API_ID,
            "api_version": (
                TENANT_SCIENTIFIC_AUTHORITY_API_VERSION
            ),
            "authorization": authorization,
            "tenant_id": tenant_id,
            "count": len(records),
            "bindings": [
                record.to_dict()
                for record in records
            ],
        }

    return router
