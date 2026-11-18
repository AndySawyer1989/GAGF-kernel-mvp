from __future__ import annotations

from dataclasses import dataclass

from backend.app.gagf.governance_agent_approval_service import (
    ApprovalIdentityProvider,
    GovernanceAgentApprovalService,
)
from backend.app.gagf.governance_agent_approval_store import (
    AgentApprovalStore,
)
from backend.app.gagf.governance_agent_approval_workflow_event_adapter import (
    GovernanceAgentApprovalWorkflowEventAdapter,
)
from backend.app.gagf.governance_agent_bounded_dispatcher import (
    AgentBoundedDispatcher,
)
from backend.app.gagf.governance_agent_event_bus import (
    GovernanceAgentEventBus,
)
from backend.app.gagf.governance_agent_orchestrator import (
    GovernanceAgentOrchestrator,
)
from backend.app.gagf.governance_agent_runtime_coordinator import (
    GovernanceAgentRuntimeCoordinator,
)
from backend.app.gagf.governance_agent_state_router import (
    GovernanceAgentStateRouter,
)
from backend.app.gagf.governance_agent_task_capability_policy import (
    AgentTaskCapabilityPolicy,
    default_engineering_task_capability_policy,
)
from backend.app.gagf.governance_agent_worker_matcher import (
    AgentWorkerMatcher,
)
from backend.app.gagf.governance_agent_worker_registry_store import (
    AgentWorkerRegistryStore,
)
from backend.app.gagf.governance_agent_work_item_store import (
    AgentWorkItemStore,
)
from backend.app.gagf.governance_agent_workflow_approval_integration import (
    GovernanceAgentWorkflowApprovalIntegration,
)
from backend.app.gagf.governance_agent_workflow_store import (
    AgentWorkflowStore,
)
from backend.app.gagf.governance_agent_workspace_manager import (
    AgentWorkspaceManager,
)

from backend.app.engineering_agent.config import (
    EngineeringAgentSettings,
)

from backend.app.engineering_agent.runtime_operations import (
    RuntimeOperationsService,
)


@dataclass(slots=True)
class EngineeringAgentContainer:
    settings: EngineeringAgentSettings

    workflow_store: AgentWorkflowStore
    work_item_store: AgentWorkItemStore
    worker_registry_store: AgentWorkerRegistryStore

    state_router: GovernanceAgentStateRouter
    worker_matcher: AgentWorkerMatcher
    capability_policy: AgentTaskCapabilityPolicy
    bounded_dispatcher: AgentBoundedDispatcher
    runtime_coordinator: GovernanceAgentRuntimeCoordinator
    runtime_operations: RuntimeOperationsService

    event_bus: GovernanceAgentEventBus
    orchestrator: GovernanceAgentOrchestrator

    approval_store: AgentApprovalStore | None = None
    approval_service: GovernanceAgentApprovalService | None = None
    workflow_approval_integration: (
        GovernanceAgentWorkflowApprovalIntegration | None
    ) = None
    approval_event_adapter: (
        GovernanceAgentApprovalWorkflowEventAdapter | None
    ) = None

    @classmethod
    def build(
        cls,
        settings: EngineeringAgentSettings,
        *,
        approval_identity_provider: ApprovalIdentityProvider | None = None,
    ) -> EngineeringAgentContainer:
        settings.data_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        timeout = settings.database_timeout_seconds

        # Workflow, work-item, and worker-registry records share
        # one database to support registered claims and tenant scope.
        workflow_store = AgentWorkflowStore(
            settings.workflow_database_path,
            timeout_seconds=timeout,
        )

        work_item_store = AgentWorkItemStore(
            settings.workflow_database_path,
            timeout_seconds=timeout,
        )

        worker_registry_store = AgentWorkerRegistryStore(
            settings.workflow_database_path,
            timeout_seconds=timeout,
        )

        state_router = GovernanceAgentStateRouter(
            workflow_store
        )

        worker_matcher = AgentWorkerMatcher(
            worker_registry_store
        )

        capability_policy = (
            default_engineering_task_capability_policy()
        )

        bounded_dispatcher = AgentBoundedDispatcher(
            work_item_store=work_item_store,
            worker_matcher=worker_matcher,
        )

        runtime_coordinator = GovernanceAgentRuntimeCoordinator(
            state_router=state_router,
            bounded_dispatcher=bounded_dispatcher,
            task_capability_policy=capability_policy,
        )

        runtime_operations = RuntimeOperationsService(
            runtime_coordinator=runtime_coordinator,
        )

        event_bus = GovernanceAgentEventBus()

        orchestrator = GovernanceAgentOrchestrator(
            event_bus=event_bus,
            state_router=state_router,
        )

        approval_store = None
        approval_service = None
        workflow_approval_integration = None
        approval_event_adapter = None

        # Approval services are composed only when a trusted
        # authentication adapter is explicitly supplied.
        if approval_identity_provider is not None:
            approval_store = AgentApprovalStore(
                settings.approval_database_path,
                timeout_seconds=timeout,
            )

            approval_service = GovernanceAgentApprovalService(
                store=approval_store,
                identity_provider=approval_identity_provider,
            )

            workflow_approval_integration = (
                GovernanceAgentWorkflowApprovalIntegration(
                    workflow_store=workflow_store,
                    approval_service=approval_service,
                )
            )

            approval_event_adapter = (
                GovernanceAgentApprovalWorkflowEventAdapter(
                    workflow_store=workflow_store,
                    approval_service=approval_service,
                    workflow_approval_integration=(
                        workflow_approval_integration
                    ),
                )
            )

        return cls(
            settings=settings,
            workflow_store=workflow_store,
            work_item_store=work_item_store,
            worker_registry_store=worker_registry_store,
            state_router=state_router,
            worker_matcher=worker_matcher,
            capability_policy=capability_policy,
            bounded_dispatcher=bounded_dispatcher,
            runtime_coordinator=runtime_coordinator,
            runtime_operations=runtime_operations,
            event_bus=event_bus,
            orchestrator=orchestrator,
            approval_store=approval_store,
            approval_service=approval_service,
            workflow_approval_integration=(
                workflow_approval_integration
            ),
            approval_event_adapter=approval_event_adapter,
        )

    def create_workspace_manager(self) -> AgentWorkspaceManager:
        """Construct the workspace manager explicitly.

        This validates the Git repository and initializes workspace
        metadata. It does not provide OS-level process isolation.
        A Git worktree must never be treated as a security sandbox.
        """
        return AgentWorkspaceManager(
            repository_path=self.settings.repository_path,
            workspace_root=self.settings.workspace_root,
            timeout_seconds=self.settings.database_timeout_seconds,
        )

    def close(self) -> None:
        """Release lifecycle-managed resources.

        Current SQLite stores open connections per operation.
        No persistent database connections need closing here.
        """
        return None