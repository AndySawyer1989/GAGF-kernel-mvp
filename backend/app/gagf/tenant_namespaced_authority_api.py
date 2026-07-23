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
from backend.app.gagf.scientific_execution_context import (
    ScientificContextBindingConflictError,
    ScientificExecutionContext,
    ScientificExecutionContextError,
)
from backend.app.gagf.tenant_artifact_namespace import (
    TenantArtifactNamespaceConflictError,
)
from backend.app.gagf.tenant_namespaced_artifact_resolver import (
    TenantNamespacedArtifactIntegrityError,
    TenantNamespacedArtifactNotFoundError,
    TenantNamespacedArtifactResolver,
    TenantNamespacedArtifactResolutionError,
)
from backend.app.gagf.tenant_namespaced_execution import (
    TenantNamespacedExecutionPaths,
    TenantNamespacedScientificExecutionService,
)
from backend.app.gagf.tenant_public_execution_view import (
    TenantPublicExecutionViewBuilder,
)
from backend.app.gagf.tenant_public_artifact_view import (
    TenantPublicArtifactViewBuilder,
)
from backend.app.gagf.tenant_public_authorization_view import (
    TenantPublicAuthorizationViewBuilder,
)
from backend.app.gagf.tenant_public_response_gate import (
    TenantPublicResponseGate,
    TenantPublicResponseRejectedError,
)


TENANT_NAMESPACED_AUTHORITY_API_ID = (
    "tenant-namespaced-scientific-authority-api"
)
TENANT_NAMESPACED_AUTHORITY_API_VERSION = "0.5.0"


@dataclass(frozen=True, slots=True)
class TenantNamespacedAuthorityApiPaths:
    authority_database_path: Path
    audit_database_path: Path
    checkpoint_database_path: Path
    journal_database_path: Path
    context_binding_database_path: Path
    namespace_database_path: Path


class NamespacedAuthorityEvidenceRequest(BaseModel):
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


class NamespacedTrustSignalsRequest(BaseModel):
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


class NamespacedAuthorityEvaluationRequest(BaseModel):
    calculation_id: str
    requested_authority: CalculationAuthority
    constitutional_approval_submitted: bool = False
    evidence: NamespacedAuthorityEvidenceRequest
    trust_signals: NamespacedTrustSignalsRequest


def create_tenant_namespaced_authority_router(
    *,
    paths: TenantNamespacedAuthorityApiPaths,
) -> APIRouter:
    router = APIRouter(
        prefix="/tenant-namespaced-scientific-authority",
        tags=["tenant-namespaced-scientific-authority"],
    )

    execution_service = (
        TenantNamespacedScientificExecutionService(
            paths=TenantNamespacedExecutionPaths(
                authority_database_path=(
                    paths.authority_database_path
                ),
                audit_database_path=paths.audit_database_path,
                checkpoint_database_path=(
                    paths.checkpoint_database_path
                ),
                journal_database_path=(
                    paths.journal_database_path
                ),
                context_binding_database_path=(
                    paths.context_binding_database_path
                ),
                namespace_database_path=(
                    paths.namespace_database_path
                ),
            )
        )
    )

    resolver = TenantNamespacedArtifactResolver(
        namespace_database_path=paths.namespace_database_path,
        authority_database_path=paths.authority_database_path,
        checkpoint_database_path=paths.checkpoint_database_path,
        journal_database_path=paths.journal_database_path,
        context_binding_database_path=(
            paths.context_binding_database_path
        ),
    )

    authorization_policy = (
        ScientificAuthorityAuthorizationPolicy()
    )
    public_view_builder = (
        TenantPublicExecutionViewBuilder()
    )
    public_artifact_view_builder = (
        TenantPublicArtifactViewBuilder()
    )
    public_authorization_view_builder = (
        TenantPublicAuthorizationViewBuilder()
    )
    public_response_gate = TenantPublicResponseGate()

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

    def authorize(
        *,
        context: ScientificExecutionContext,
        action: ScientificAuthorityAction,
        trust_signals: ScientificTrustSignals,
        requested_authority: CalculationAuthority | None = None,
        constitutional_approval_submitted: bool = False,
    ) -> dict:
        request = ScientificAuthorizationRequest(
            context=context,
            action=action,
            target_tenant_id=context.tenant_id,
            requested_authority=requested_authority,
            constitutional_approval_submitted=(
                constitutional_approval_submitted
            ),
            trust_signals=trust_signals,
        )

        decision, receipt = (
            authorization_policy.evaluate_with_receipt(
                request
            )
        )

        public_authorization = (
            public_authorization_view_builder.build(
                decision=decision,
                receipt=receipt,
            )
        )

        if not decision.allowed:
            detail = {
                "message": (
                    "Tenant namespaced scientific request "
                    "was denied."
                ),
                **public_authorization.to_dict(),
            }

            try:
                released_detail = (
                    public_response_gate
                    .release_error_detail(
                        detail=detail
                    )
                )
            except TenantPublicResponseRejectedError as exc:
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Tenant response failed public-boundary "
                        "validation."
                    ),
                ) from exc

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=released_detail,
            )

        return public_authorization.to_dict()

    def header_trust(
        *,
        credential_verified: bool,
        session_verified: bool,
        device_trusted: bool,
        tenant_membership_verified: bool,
    ) -> ScientificTrustSignals:
        return ScientificTrustSignals(
            credential_verified=credential_verified,
            session_verified=session_verified,
            device_trusted=device_trusted,
            step_up_verified=False,
            tenant_membership_verified=(
                tenant_membership_verified
            ),
        )

    def resolve_or_raise(
        *,
        tenant_id: str,
        artifact_type: str,
        public_id: str,
    ) -> dict:
        try:
            resolution = resolver.resolve(
                tenant_id=tenant_id,
                artifact_type=artifact_type,
                namespaced_artifact_id=public_id,
            )
        except TenantNamespacedArtifactNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except TenantNamespacedArtifactIntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except TenantNamespacedArtifactResolutionError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        public_view = public_artifact_view_builder.build(
            resolution=resolution
        )

        return public_view.to_dict()

    def release_public_response(
        response: dict,
    ) -> dict:
        try:
            return public_response_gate.release(
                response=response
            )
        except TenantPublicResponseRejectedError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=str(exc),
            ) from exc
    @router.post(
        "/evaluate",
        status_code=status.HTTP_200_OK,
    )
    def evaluate(
        request: NamespacedAuthorityEvaluationRequest,
        x_tenant_id: str = Header(...),
        x_actor_id: str = Header(...),
        x_credential_id: str = Header(...),
        x_session_id: str = Header(...),
        x_role_id: str = Header(...),
        x_policy_scope: str = Header(...),
        x_request_id: str = Header(...),
        x_correlation_id: str = Header(...),
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
            result = execution_service.execute(
                context=context,
                contract=contract,
                requested_authority=(
                    request.requested_authority
                ),
                evidence=request.evidence.to_domain(),
            )

            public_view = public_view_builder.build(
                result=result
            )
        except (
            ScientificContextBindingConflictError,
            TenantArtifactNamespaceConflictError,
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Tenant namespaced scientific execution "
                    "failed: "
                    + str(exc)
                ),
            ) from exc

        public_artifacts = {
            "execution_id": (
                result.namespace_bundle.execution
                .namespaced_artifact_id
            ),
            "execution_receipt_id": (
                result.namespace_bundle.execution_receipt
                .namespaced_artifact_id
            ),
            "authority_receipt_id": (
                result.namespace_bundle.authority_receipt
                .namespaced_artifact_id
            ),
            "audit_receipt_id": (
                result.namespace_bundle.audit_receipt
                .namespaced_artifact_id
            ),
            "checkpoint_id": (
                result.namespace_bundle.checkpoint
                .namespaced_artifact_id
            ),
            "context_binding_id": (
                result.namespace_bundle.context_binding
                .namespaced_artifact_id
            ),
        }

        return release_public_response(
            {
                "api_id": TENANT_NAMESPACED_AUTHORITY_API_ID,
                "api_version": (
                    TENANT_NAMESPACED_AUTHORITY_API_VERSION
                ),
                "tenant_id": context.tenant_id,
                "authorization": authorization,
                "public_artifacts": public_artifacts,
                "execution": public_view.to_dict(),
            }
        )

    def build_read_context(
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
        return build_context(
            tenant_id=tenant_id,
            actor_id=actor_id,
            credential_id=credential_id,
            session_id=session_id,
            role_id=role_id,
            policy_scope=policy_scope,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    @router.get("/receipts/{public_id}")
    def get_receipt(
        public_id: str,
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
        context = build_read_context(
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
            trust_signals=header_trust(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        return release_public_response(
            {
                "api_id": TENANT_NAMESPACED_AUTHORITY_API_ID,
                "api_version": (
                    TENANT_NAMESPACED_AUTHORITY_API_VERSION
                ),
                "authorization": authorization,
                **resolve_or_raise(
                    tenant_id=x_tenant_id,
                    artifact_type="authority_receipt",
                    public_id=public_id,
                ),
            }
        )

    @router.get("/checkpoints/{public_id}")
    def get_checkpoint(
        public_id: str,
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
        context = build_read_context(
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
            trust_signals=header_trust(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        return release_public_response(
            {
                "api_id": TENANT_NAMESPACED_AUTHORITY_API_ID,
                "api_version": (
                    TENANT_NAMESPACED_AUTHORITY_API_VERSION
                ),
                "authorization": authorization,
                **resolve_or_raise(
                    tenant_id=x_tenant_id,
                    artifact_type="checkpoint",
                    public_id=public_id,
                ),
            }
        )

    @router.get("/executions/{public_id}")
    def get_execution(
        public_id: str,
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
        context = build_read_context(
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
            trust_signals=header_trust(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        return release_public_response(
            {
                "api_id": TENANT_NAMESPACED_AUTHORITY_API_ID,
                "api_version": (
                    TENANT_NAMESPACED_AUTHORITY_API_VERSION
                ),
                "authorization": authorization,
                **resolve_or_raise(
                    tenant_id=x_tenant_id,
                    artifact_type="execution",
                    public_id=public_id,
                ),
            }
        )

    @router.get("/bindings/{public_id}")
    def get_binding(
        public_id: str,
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
        context = build_read_context(
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
            trust_signals=header_trust(
                credential_verified=x_credential_verified,
                session_verified=x_session_verified,
                device_trusted=x_device_trusted,
                tenant_membership_verified=(
                    x_tenant_membership_verified
                ),
            ),
        )

        return release_public_response(
            {
                "api_id": TENANT_NAMESPACED_AUTHORITY_API_ID,
                "api_version": (
                    TENANT_NAMESPACED_AUTHORITY_API_VERSION
                ),
                "authorization": authorization,
                **resolve_or_raise(
                    tenant_id=x_tenant_id,
                    artifact_type="context_binding",
                    public_id=public_id,
                ),
            }
        )

    return router






