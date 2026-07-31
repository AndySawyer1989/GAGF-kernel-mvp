from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import Depends, FastAPI

from backend.app.gagf.governance_assessment_api import (
    create_governance_assessment_router,
)
from backend.app.gagf.governance_assessment_application import (
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_audit import (
    AssessmentAuditLedger,
)
from backend.app.gagf.governance_assessment_audit_api import (
    create_governance_assessment_audit_router,
)
from backend.app.gagf.governance_assessment_audit_checkpoint import (
    AssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_audit_checkpoint_signature_store import (
    SignedAssessmentAuditCheckpointStore,
)
from backend.app.gagf.governance_assessment_audit_middleware import (
    install_assessment_audit_middleware,
)
from backend.app.gagf.governance_assessment_auth import (
    require_assessment_actor,
)
from backend.app.gagf.governance_assessment_checkpoint_key_bootstrap import (
    AssessmentCheckpointKeyBootstrapConfig,
    build_assessment_checkpoint_key_service,
)
from backend.app.gagf.governance_assessment_checkpoint_key_admin_api import (
    create_assessment_checkpoint_key_admin_router,
)
from backend.app.gagf.governance_assessment_checkpoint_key_audit import (
    AssessmentCheckpointKeyAuditStore,
)
from backend.app.gagf.governance_assessment_checkpoint_key_config import (
    load_assessment_checkpoint_production_key_config,
)
from backend.app.gagf.governance_assessment_dashboard import (
    GovernanceAssessmentDashboardService,
)
from backend.app.gagf.governance_assessment_dashboard_api import (
    create_governance_assessment_dashboard_router,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)


ASSESSMENT_API_REGISTRATION_VERSION = "1.1.0"
ASSESSMENT_API_REGISTERED_STATE_KEY = (
    "governance_assessment_api_registered"
)


class AssessmentApiRegistrationError(RuntimeError):
    """Raised when the assessment API cannot be registered."""


def register_governance_assessment_api(
    *,
    app: FastAPI,
    repository: GovernanceAssessmentRepository | None = None,
    database_path: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> GovernanceAssessmentApplicationService:
    if repository is not None and database_path is not None:
        raise AssessmentApiRegistrationError(
            "provide repository or database_path, not both"
        )

    existing_service = getattr(
        app.state,
        "governance_assessment_service",
        None,
    )
    already_registered = bool(
        getattr(
            app.state,
            ASSESSMENT_API_REGISTERED_STATE_KEY,
            False,
        )
    )

    if already_registered:
        if existing_service is None:
            raise AssessmentApiRegistrationError(
                "assessment API registration state is inconsistent"
            )

        return existing_service

    resolved_repository = repository

    if resolved_repository is None:
        if database_path is None:
            raise AssessmentApiRegistrationError(
                "repository or database_path is required"
            )

        resolved_path = Path(database_path)
        resolved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        resolved_repository = GovernanceAssessmentRepository(
            resolved_path
        )

    assessment_database_path = database_path

    if assessment_database_path is None:
        assessment_database_path = getattr(
            resolved_repository,
            "database_path",
            None,
        )

    if assessment_database_path is None:
        raise AssessmentApiRegistrationError(
            "assessment database path could not be resolved"
        )

    assessment_database_path = Path(
        assessment_database_path
    )
    resolved_environment = (
        environment
        if environment is not None
        else os.environ
    )

    service = GovernanceAssessmentApplicationService(
        repository=resolved_repository
    )
    router = create_governance_assessment_router(
        service=service,
        dependencies=[Depends(require_assessment_actor)],
    )
    app.router.routes.extend(router.routes)

    audit_database_path = assessment_database_path.with_name(
        "governance_assessment_audit.sqlite3"
    )
    audit_ledger = AssessmentAuditLedger(
        audit_database_path
    )
    install_assessment_audit_middleware(
        app=app,
        ledger=audit_ledger,
    )

    checkpoint_database_path = (
        assessment_database_path.with_name(
            "governance_assessment_audit_checkpoints.sqlite3"
        )
    )
    checkpoint_store = AssessmentAuditCheckpointStore(
        checkpoint_database_path
    )

    signed_checkpoint_database_path = (
        assessment_database_path.with_name(
            "governance_assessment_signed_checkpoints.sqlite3"
        )
    )
    signed_checkpoint_store = (
        SignedAssessmentAuditCheckpointStore(
            signed_checkpoint_database_path
        )
    )

    checkpoint_key_audit_database_path = (
        assessment_database_path.with_name(
            "governance_assessment_checkpoint_key_audit.sqlite3"
        )
    )
    checkpoint_key_audit_store = (
        AssessmentCheckpointKeyAuditStore(
            checkpoint_key_audit_database_path
        )
    )

    durable_key_service = None
    bootstrap_result = None

    try:
        production_key_config = (
            load_assessment_checkpoint_production_key_config(
                assessment_database_path=assessment_database_path,
                environment=resolved_environment,
            )
        )

        if production_key_config.enabled:
            bootstrap_result = (
                build_assessment_checkpoint_key_service(
                    config=AssessmentCheckpointKeyBootstrapConfig(
                        metadata_database_path=(
                            production_key_config.metadata_database_path
                        ),
                        tenant_id=production_key_config.tenant_id,
                        key_id=production_key_config.key_id,
                        secret_reference=(
                            production_key_config.secret_reference
                        ),
                        make_active=True,
                    ),
                    environment=resolved_environment,
                )
            )
            durable_key_service = bootstrap_result.service
    except (KeyError, ValueError) as error:
        raise AssessmentApiRegistrationError(
            "assessment checkpoint signing configuration is invalid"
        ) from error

    audit_router = create_governance_assessment_audit_router(
        ledger=audit_ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_checkpoint_store,
        durable_checkpoint_key_service=durable_key_service,
    )
    app.router.routes.extend(audit_router.routes)

    dashboard_service = GovernanceAssessmentDashboardService(
        audit_ledger=audit_ledger,
        checkpoint_store=checkpoint_store,
        signed_checkpoint_store=signed_checkpoint_store,
        key_metadata_store=(
            bootstrap_result.metadata_store
            if bootstrap_result is not None
            else None
        ),
        key_audit_store=checkpoint_key_audit_store,
    )
    dashboard_router = (
        create_governance_assessment_dashboard_router(
            dashboard_service=dashboard_service
        )
    )
    app.router.routes.extend(dashboard_router.routes)

    if (
        durable_key_service is not None
        and bootstrap_result is not None
    ):
        checkpoint_key_admin_router = (
            create_assessment_checkpoint_key_admin_router(
                metadata_store=bootstrap_result.metadata_store,
                key_service=durable_key_service,
                audit_store=checkpoint_key_audit_store,
            )
        )
        app.router.routes.extend(
            checkpoint_key_admin_router.routes
        )

    app.state.governance_assessment_repository = (
        resolved_repository
    )
    app.state.governance_assessment_service = service
    app.state.governance_assessment_audit_ledger = audit_ledger
    app.state.governance_assessment_checkpoint_store = (
        checkpoint_store
    )
    app.state.governance_assessment_signed_checkpoint_store = (
        signed_checkpoint_store
    )
    app.state.governance_assessment_checkpoint_key_audit_store = (
        checkpoint_key_audit_store
    )
    app.state.governance_assessment_dashboard_service = (
        dashboard_service
    )
    app.state.governance_assessment_checkpoint_key_service = (
        durable_key_service
    )

    setattr(
        app.state,
        ASSESSMENT_API_REGISTERED_STATE_KEY,
        True,
    )

    return service
