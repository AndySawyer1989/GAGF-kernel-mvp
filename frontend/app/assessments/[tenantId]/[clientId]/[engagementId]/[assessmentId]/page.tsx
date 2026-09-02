"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";
import {
  AssessmentReadinessPanel,
  type AssessmentReadinessItem
} from "@/components/assessment-readiness-panel";
import {
  AssessmentWorkflowShell,
  type AssessmentWorkflowStep
} from "@/components/assessment-workflow-shell";
import {
  PaidAssessmentExecutionAuthorization,
  type PaidAssessmentExecutionAuthorizationValue
} from "@/components/paid-assessment-execution-authorization";
import {
  AssessmentDeliveryStatus
} from "@/components/assessment-delivery-status";
import {
  DiagnosticFindingsSummary
} from "@/components/diagnostic-findings-summary";
import {
  GovernanceFrictionMap,
  type GovernanceFrictionMapItem
} from "@/components/governance-friction-map";
import {
  AssessmentCloseoutPanel
} from "@/components/assessment-closeout-panel";
import {
  GovernanceInterventionPlan,
  type GovernanceInterventionPlanItem
} from "@/components/governance-intervention-plan";
import {
  GovernanceRoadmap,
  type GovernanceRoadmapPhase
} from "@/components/governance-roadmap";
import {
  executePaidAssessment,
  fetchAssessment,
  fetchAssessmentArtifacts,
  fetchAssessmentSummary,
  fetchPaidAssessmentExecutionInputBinding,
  fetchPaidAssessmentExecutionStatus,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type CommercialPaidAssessmentDisposition,
  type CommercialPaidAssessmentExecutionInputBindingMetadata,
  type GovernanceAssessmentArtifact,
  type GovernanceAssessmentArtifactList,
  type GovernanceAssessmentIdentity,
  type GovernanceAssessmentRecord,
  type GovernanceAssessmentSummary
} from "@/lib/governance-assessment-api";

function textValue(
  payload: Record<string, unknown> | undefined,
  key: string
): string | null {
  const value = payload?.[key];

  return typeof value === "string"
    ? value
    : null;
}

function numberValue(
  payload: Record<string, unknown> | undefined,
  key: string
): number | null {
  const value = payload?.[key];

  return typeof value === "number"
    ? value
    : null;
}

function booleanValue(
  payload: Record<string, unknown> | undefined,
  key: string
): boolean | null {
  const value = payload?.[key];

  return typeof value === "boolean"
    ? value
    : null;
}

function stringArray(
  payload: Record<string, unknown> | undefined,
  key: string
): string[] {
  const value = payload?.[key];

  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(
    (item): item is string =>
      typeof item === "string"
  );
}

function objectArray(
  payload: Record<string, unknown> | undefined,
  key: string
): Record<string, unknown>[] {
  const value = payload?.[key];

  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(
    (item): item is Record<string, unknown> =>
      typeof item === "object" &&
      item !== null
  );
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function findArtifact(
  artifacts: GovernanceAssessmentArtifactList | null,
  artifactType: string
): GovernanceAssessmentArtifact | undefined {
  return artifacts?.items.find(
    (artifact) =>
      artifact.artifact_type === artifactType
  );
}

const CLIENT_REPORT_ARTIFACT_TYPE =
  "client-report-package";

function ResultMetric({
  label,
  value,
  detail
}: {
  label: string;
  value: string | number;
  detail: string;
}) {
  return (
    <article className="result-metric">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

const EMPTY_PAID_EXECUTION_AUTHORIZATION:
  PaidAssessmentExecutionAuthorizationValue = {
    operatorName: "",
    clientContactName: "",
    classification: "non_sensitive",

    assessmentScopeConfirmed: false,
    evidenceScopeConfirmed: false,
    clientDataUseConfirmed: false,
    operatorReadinessConfirmed: false,

    clientAuthorizedForAssessment: false,
    minimizationReviewCompleted: false,
    directIdentifiersRemoved: false,

    operatorControlledLocation: false,
    accessRestricted: false,
    storageProtectionConfirmed: false,
    backupPlanRecorded: false,
    retentionPeriodRecorded: false,
    deletionPlanRecorded: false,

    contractExecuted: false,
    contractExecutionReviewReady: false,
    contractExecutionConfirmed: false,
    executedContractReferenceRecorded: false,
    executedAtRecorded: false,
    allRequiredSignaturesRecorded: false,
    humanOperatorConfirmedExecution: false,

    paidAssessmentAuthorized: false,
    executionEvidenceApproved: false
  };


export default function AssessmentDetailPage() {
  const params = useParams<{
    tenantId: string;
    clientId: string;
    engagementId: string;
    assessmentId: string;
  }>();

  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const identity =
    useMemo<GovernanceAssessmentIdentity>(
      () => ({
        tenantId: decodeURIComponent(
          params.tenantId
        ),
        clientId: decodeURIComponent(
          params.clientId
        ),
        engagementId: decodeURIComponent(
          params.engagementId
        ),
        assessmentId: decodeURIComponent(
          params.assessmentId
        )
      }),
      [params]
    );

  const [assessment, setAssessment] =
    useState<GovernanceAssessmentRecord | null>(
      null
    );
  const [summary, setSummary] =
    useState<GovernanceAssessmentSummary | null>(
      null
    );
  const [artifacts, setArtifacts] =
    useState<GovernanceAssessmentArtifactList | null>(
      null
    );
  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);

  const [
    executionBinding,
    setExecutionBinding
  ] =
    useState<
      CommercialPaidAssessmentExecutionInputBindingMetadata | null
    >(null);

  const [
    bindingLoading,
    setBindingLoading
  ] =
    useState(true);

  const [
    bindingError,
    setBindingError
  ] =
    useState<string | null>(
      null
    );

  const [
    executionAuthorization,
    setExecutionAuthorization
  ] =
    useState<
      PaidAssessmentExecutionAuthorizationValue
    >(
      EMPTY_PAID_EXECUTION_AUTHORIZATION
    );

  const [
    diagnosticRunning,
    setDiagnosticRunning
  ] =
    useState(false);

  const [
    diagnosticDisposition,
    setDiagnosticDisposition
  ] =
    useState<
      CommercialPaidAssessmentDisposition | null
    >(null);

  const [
    diagnosticExecutionError,
    setDiagnosticExecutionError
  ] =
    useState<string | null>(
      null
    );

  const [
    executionStatusLoading,
    setExecutionStatusLoading
  ] =
    useState(true);

  const [
    executionStatusError,
    setExecutionStatusError
  ] =
    useState<string | null>(
      null
    );

  const loadAssessment = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const [
          assessmentResult,
          summaryResult,
          artifactResult
        ] = await Promise.all([
          fetchAssessment(
            config,
            identity,
            signal
          ),
          fetchAssessmentSummary(
            config,
            identity,
            signal
          ),
          fetchAssessmentArtifacts(
            config,
            identity,
            signal
          )
        ]);

        setAssessment(assessmentResult);
        setSummary(summaryResult);
        setArtifacts(artifactResult);
      } catch (caught) {
        if (
          caught instanceof DOMException &&
          caught.name === "AbortError"
        ) {
          return;
        }

        if (
          caught instanceof GovernanceAssessmentApiError
        ) {
          setError(
            `Backend returned ${caught.status}. The assessment may not exist or may not be visible to this tenant.`
          );
        } else {
          setError(
            "The assessment results could not be loaded."
          );
        }
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [config, identity]
  );

  useEffect(() => {
    const controller = new AbortController();

    void loadAssessment(controller.signal);

    return () => controller.abort();
  }, [loadAssessment]);

  useEffect(() => {
    const controller =
      new AbortController();

    async function loadExecutionBinding() {
      setBindingLoading(true);
      setBindingError(null);

      try {
        const result =
          await fetchPaidAssessmentExecutionInputBinding(
            config,
            identity,
            controller.signal
          );

        if (
          !controller.signal.aborted
        ) {
          setExecutionBinding(
            result
          );
        }
      } catch (caught) {
        if (
          caught instanceof DOMException &&
          caught.name === "AbortError"
        ) {
          return;
        }

        if (
          controller.signal.aborted
        ) {
          return;
        }

        setExecutionBinding(
          null
        );

        if (
          caught instanceof
          GovernanceAssessmentApiError
        ) {
          setBindingError(
            `Execution binding unavailable. Backend returned ${caught.status}.`
          );
        } else {
          setBindingError(
            "Execution binding could not be loaded."
          );
        }
      } finally {
        if (
          !controller.signal.aborted
        ) {
          setBindingLoading(
            false
          );
        }
      }
    }

    void loadExecutionBinding();

    return () =>
      controller.abort();
  }, [config, identity]);

  useEffect(() => {
    const controller =
      new AbortController();

    async function loadExecutionStatus() {
      setExecutionStatusLoading(true);
      setExecutionStatusError(null);

      try {
        const result =
          await fetchPaidAssessmentExecutionStatus(
            config,
            identity,
            controller.signal
          );

        if (
          controller.signal.aborted
        ) {
          return;
        }

        if (
          result.found &&
          result.status !== null
        ) {
          setDiagnosticDisposition(
            result.status.disposition
          );
        } else {
          setDiagnosticDisposition(
            null
          );
        }
      } catch (caught) {
        if (
          caught instanceof DOMException &&
          caught.name === "AbortError"
        ) {
          return;
        }

        if (
          controller.signal.aborted
        ) {
          return;
        }

        setDiagnosticDisposition(
          null
        );

        if (
          caught instanceof
          GovernanceAssessmentApiError
        ) {
          setExecutionStatusError(
            `Paid execution status unavailable. Backend returned ${caught.status}.`
          );
        } else {
          setExecutionStatusError(
            "Paid execution status could not be loaded."
          );
        }
      } finally {
        if (
          !controller.signal.aborted
        ) {
          setExecutionStatusLoading(
            false
          );
        }
      }
    }

    void loadExecutionStatus();

    return () =>
      controller.abort();
  }, [config, identity]);

  const qualityArtifact = findArtifact(
    artifacts,
    "evidence-quality"
  );
  const frictionArtifact = findArtifact(
    artifacts,
    "friction-summary"
  );
  const debtArtifact = findArtifact(
    artifacts,
    "governance-debt-score"
  );
  const interventionArtifact = findArtifact(
    artifacts,
    "intervention-plan"
  );
  const roadmapArtifact = findArtifact(
    artifacts,
    "assessment-roadmap"
  );
  const projectionArtifact = findArtifact(
    artifacts,
    "executive-projection"
  );

  const qualityScore =
    numberValue(
      qualityArtifact?.payload,
      "quality_score"
    ) ?? 0;

  const qualityGrade =
    textValue(
      qualityArtifact?.payload,
      "quality_grade"
    ) ?? "unknown";

  const debtScore =
    numberValue(
      debtArtifact?.payload,
      "score"
    ) ?? 0;

  const debtBand =
    textValue(
      debtArtifact?.payload,
      "band"
    ) ?? "unknown";

  const dominantConstraint =
    textValue(
      frictionArtifact?.payload,
      "dominant_constraint"
    ) ?? "Not identified";

  const totalFriction =
    numberValue(
      frictionArtifact?.payload,
      "total_friction_score"
    ) ?? 0;
  const constraintAggregations = objectArray(
    frictionArtifact?.payload,
    "constraint_aggregations"
  );

  const recognizedConstraintEvents =
    numberValue(
      frictionArtifact?.payload,
      "recognized_constraint_events"
    ) ?? 0;

  const frictionUniqueWorkItemCount =
    numberValue(
      frictionArtifact?.payload,
      "unique_work_item_count"
    ) ?? 0;

  const frictionMapItems: GovernanceFrictionMapItem[] =
    constraintAggregations.flatMap(
      (aggregation) => {
        const category = textValue(
          aggregation,
          "category"
        );

        const eventCount = numberValue(
          aggregation,
          "event_count"
        );

        const uniqueWorkItemCount = numberValue(
          aggregation,
          "unique_work_item_count"
        );

        const firstOccurredAt = textValue(
          aggregation,
          "first_occurred_at"
        );

        const lastOccurredAt = textValue(
          aggregation,
          "last_occurred_at"
        );

        const weight = numberValue(
          aggregation,
          "weight"
        );

        const frictionScore = numberValue(
          aggregation,
          "friction_score"
        );

        const eventShare = numberValue(
          aggregation,
          "event_share"
        );

        const band = textValue(
          aggregation,
          "band"
        );

        if (
          category === null ||
          eventCount === null ||
          uniqueWorkItemCount === null ||
          firstOccurredAt === null ||
          lastOccurredAt === null ||
          weight === null ||
          frictionScore === null ||
          eventShare === null ||
          band === null
        ) {
          return [];
        }

        return [
          {
            category,
            eventCount,
            uniqueWorkItemCount,
            firstOccurredAt,
            lastOccurredAt,
            weight,
            frictionScore,
            eventShare,
            band,
            isDominant:
              category === dominantConstraint
          }
        ];
      }
    );

  const executiveSummary =
    textValue(
      projectionArtifact?.payload,
      "executive_summary"
    );

  const findings = stringArray(
    projectionArtifact?.payload,
    "key_findings"
  );

  const interventionCandidates = objectArray(
    interventionArtifact?.payload,
    "interventions"
  );

  const interventionGovernanceDebtScore =
    numberValue(
      interventionArtifact?.payload,
      "governance_debt_score"
    ) ?? 0;

  const topInterventionId = textValue(
    interventionArtifact?.payload,
    "top_intervention_id"
  );

  const interventionPlanHash = textValue(
    interventionArtifact?.payload,
    "plan_hash"
  );

  const interventionSchemaVersion = textValue(
    interventionArtifact?.payload,
    "schema_version"
  );

  const interventionPlanItems:
    GovernanceInterventionPlanItem[] =
    interventionCandidates.flatMap(
      (candidate) => {
        const interventionId = textValue(
          candidate,
          "intervention_id"
        );

        const interventionType = textValue(
          candidate,
          "intervention_type"
        );

        const title = textValue(
          candidate,
          "title"
        );

        const constraintCategory = textValue(
          candidate,
          "constraint_category"
        );

        const priority = textValue(
          candidate,
          "priority"
        );

        const rank = numberValue(
          candidate,
          "rank"
        );

        const valueScore = numberValue(
          candidate,
          "value_score"
        );

        const expectedFrictionReduction =
          numberValue(
            candidate,
            "expected_friction_reduction"
          );

        const evidenceConfidence =
          numberValue(
            candidate,
            "evidence_confidence"
          );

        const affectedWorkReach =
          numberValue(
            candidate,
            "affected_work_reach"
          );

        const implementationBurden =
          numberValue(
            candidate,
            "implementation_burden"
          );

        const reversibility =
          numberValue(
            candidate,
            "reversibility"
          );

        if (
          interventionId === null ||
          interventionType === null ||
          title === null ||
          constraintCategory === null ||
          priority === null ||
          rank === null ||
          valueScore === null ||
          expectedFrictionReduction === null ||
          evidenceConfidence === null ||
          affectedWorkReach === null ||
          implementationBurden === null ||
          reversibility === null
        ) {
          return [];
        }

        return [
          {
            interventionId,
            interventionType,
            title,
            constraintCategory,
            priority,
            rank,
            valueScore,
            expectedFrictionReduction,
            evidenceConfidence,
            affectedWorkReach,
            implementationBurden,
            reversibility,
            rationale: stringArray(
              candidate,
              "rationale"
            ),
            isTopIntervention:
              interventionId ===
              topInterventionId
          }
        ];
      }
    );
  const roadmapPhases = objectArray(
    roadmapArtifact?.payload,
    "phases"
  );

  const roadmapTotalItems =
    numberValue(
      roadmapArtifact?.payload,
      "total_items"
    ) ?? 0;

  const roadmapInterventionPlanHash =
    textValue(
      roadmapArtifact?.payload,
      "intervention_plan_hash"
    );

  const roadmapHash = textValue(
    roadmapArtifact?.payload,
    "roadmap_hash"
  );

  const roadmapSchemaVersion = textValue(
    roadmapArtifact?.payload,
    "schema_version"
  );

  const governanceRoadmapPhases:
    GovernanceRoadmapPhase[] =
    roadmapPhases.flatMap(
      (phase) => {
        const horizon = textValue(
          phase,
          "horizon"
        );

        const objective = textValue(
          phase,
          "objective"
        );

        const itemCount = numberValue(
          phase,
          "item_count"
        );

        if (
          horizon === null ||
          objective === null ||
          itemCount === null
        ) {
          return [];
        }

        const items = objectArray(
          phase,
          "items"
        ).flatMap(
          (item) => {
            const roadmapItemId = textValue(
              item,
              "roadmap_item_id"
            );

            const interventionId = textValue(
              item,
              "intervention_id"
            );

            const interventionType = textValue(
              item,
              "intervention_type"
            );

            const title = textValue(
              item,
              "title"
            );

            const itemHorizon = textValue(
              item,
              "horizon"
            );

            const sequence = numberValue(
              item,
              "sequence"
            );

            const ownerRole = textValue(
              item,
              "owner_role"
            );

            const measurableOutcome = textValue(
              item,
              "measurable_outcome"
            );

            const valueScore = numberValue(
              item,
              "value_score"
            );

            const implementationBurden =
              numberValue(
                item,
                "implementation_burden"
              );

            const status = textValue(
              item,
              "status"
            );

            if (
              roadmapItemId === null ||
              interventionId === null ||
              interventionType === null ||
              title === null ||
              itemHorizon === null ||
              sequence === null ||
              ownerRole === null ||
              measurableOutcome === null ||
              valueScore === null ||
              implementationBurden === null ||
              status === null
            ) {
              return [];
            }

            return [
              {
                roadmapItemId,
                interventionId,
                interventionType,
                title,
                horizon: itemHorizon,
                sequence,
                ownerRole,
                measurableOutcome,
                valueScore,
                implementationBurden,
                dependencyIds: stringArray(
                  item,
                  "dependency_ids"
                ),
                status
              }
            ];
          }
        );

        return [
          {
            horizon,
            objective,
            itemCount,
            items
          }
        ];
      }
    );
  const priorities = objectArray(
    projectionArtifact?.payload,
    "priorities"
  );

  const readyForAnalysis =
    booleanValue(
      qualityArtifact?.payload,
      "ready_for_analysis"
    ) ?? false;
const diagnosticArtifactsReady =
  Boolean(qualityArtifact) &&
  Boolean(frictionArtifact) &&
  Boolean(debtArtifact) &&
  Boolean(projectionArtifact);

const interventionPrioritiesReady =
  Boolean(interventionArtifact) &&
  priorities.length > 0;

const repositoryIntegrityReady =
  summary?.repository_chain_valid === true &&
  summary.artifact_count === artifacts?.count;

const clientReportArtifact = findArtifact(
  artifacts,
  CLIENT_REPORT_ARTIFACT_TYPE
);

const clientReportReady = Boolean(
  clientReportArtifact
);

const readinessItems: AssessmentReadinessItem[] = [
  {
    id: "evidence",
    label: "Evidence",
    description:
      "Evidence passed the governed quality gate and is available for analysis.",
    state: readyForAnalysis
      ? "ready"
      : "review",
    readyLabel: "Evidence ready",
    reviewLabel: "Evidence review required"
  },
  {
    id: "diagnostics",
    label: "Diagnostic artifacts",
    description:
      "Evidence quality, friction, governance debt, and executive projection artifacts are present.",
    state: diagnosticArtifactsReady
      ? "ready"
      : "review",
    readyLabel: "Diagnostics complete",
    reviewLabel: "Diagnostics incomplete"
  },
  {
    id: "interventions",
    label: "Intervention priorities",
    description:
      "A governed intervention plan and ranked priorities are available.",
    state: interventionPrioritiesReady
      ? "ready"
      : "review",
    readyLabel: "Priorities ready",
    reviewLabel: "Priorities unavailable"
  },
  {
    id: "repository",
    label: "Repository integrity",
    description:
      "The artifact chain is valid and the summary inventory matches the loaded repository inventory.",
    state: repositoryIntegrityReady
      ? "ready"
      : "review",
    readyLabel: "Repository verified",
    reviewLabel: "Integrity review required"
  },
  {
    id: "report",
    label: "Client report",
    description:
      "The governed client-report package is present in the assessment artifact chain.",
    state: clientReportReady
      ? "ready"
      : "review",
    readyLabel: "Report ready",
    reviewLabel: "Report unavailable"
  }
];

  const findingsReady =
    Boolean(projectionArtifact) &&
    findings.length > 0;

  const evidenceHref =
    "/evidence/"
    + encodeURIComponent(identity.tenantId)
    + "/"
    + encodeURIComponent(identity.clientId)
    + "/"
    + encodeURIComponent(identity.engagementId)
    + "/"
    + encodeURIComponent(identity.assessmentId);

  const reportHref =
    "/assessments/"
    + encodeURIComponent(identity.tenantId)
    + "/"
    + encodeURIComponent(identity.clientId)
    + "/"
    + encodeURIComponent(identity.engagementId)
    + "/"
    + encodeURIComponent(identity.assessmentId)
    + "/report";

  const paidDiagnosticComplete =
    diagnosticDisposition !== null;

  const workflowCompletion = [
    true,
    readyForAnalysis,
    paidDiagnosticComplete,
    paidDiagnosticComplete &&
      findingsReady,
    paidDiagnosticComplete &&
      clientReportReady
  ];

  const currentWorkflowIndex =
    workflowCompletion.findIndex(
      (complete) => !complete
    );

  function workflowState(
    index: number
  ): AssessmentWorkflowStep["state"] {
    if (workflowCompletion[index]) {
      return "complete";
    }

    if (index === currentWorkflowIndex) {
      return "current";
    }

    return "upcoming";
  }

  const workflowSteps:
    AssessmentWorkflowStep[] = [
      {
        id: "intake",
        label: "Evidence Intake",
        description:
          "Assessment evidence has entered the governed assessment record.",
        state: workflowState(0)
      },
      {
        id: "validate",
        label: "Validate Evidence",
        description:
          "Evidence must satisfy the governed quality gate before analysis.",
        state: workflowState(1)
      },
      {
        id: "diagnostic",
        label: "Run Diagnostic",
        description:
          "FIP must persist the governed diagnostic artifact set.",
        state: workflowState(2)
      },
      {
        id: "findings",
        label: "Review Findings",
        description:
          "Review governed findings, friction signals, and supporting evidence.",
        state: workflowState(3)
      },
      {
        id: "report",
        label: "Generate Report",
        description:
          "A governed client-report package must exist before delivery.",
        state: workflowState(4)
      }
    ];
  const executionAuthorizationComplete =
    executionBinding !== null &&
    executionBinding.evidence.length >
      0 &&
    executionAuthorization.operatorName
      .trim()
      .length > 0 &&
    executionAuthorization.clientContactName
      .trim()
      .length > 0 &&
    executionAuthorization.classification
      .trim()
      .length > 0 &&
    executionAuthorization
      .assessmentScopeConfirmed &&
    executionAuthorization
      .evidenceScopeConfirmed &&
    executionAuthorization
      .clientDataUseConfirmed &&
    executionAuthorization
      .operatorReadinessConfirmed &&
    executionAuthorization
      .clientAuthorizedForAssessment &&
    executionAuthorization
      .minimizationReviewCompleted &&
    executionAuthorization
      .directIdentifiersRemoved &&
    executionAuthorization
      .operatorControlledLocation &&
    executionAuthorization
      .accessRestricted &&
    executionAuthorization
      .storageProtectionConfirmed &&
    executionAuthorization
      .backupPlanRecorded &&
    executionAuthorization
      .retentionPeriodRecorded &&
    executionAuthorization
      .deletionPlanRecorded &&
    executionAuthorization
      .contractExecuted &&
    executionAuthorization
      .contractExecutionReviewReady &&
    executionAuthorization
      .contractExecutionConfirmed &&
    executionAuthorization
      .executedContractReferenceRecorded &&
    executionAuthorization
      .executedAtRecorded &&
    executionAuthorization
      .allRequiredSignaturesRecorded &&
    executionAuthorization
      .humanOperatorConfirmedExecution &&
    executionAuthorization
      .paidAssessmentAuthorized &&
    executionAuthorization
      .executionEvidenceApproved;

  const canRunDiagnostic =
    readyForAnalysis &&
    executionAuthorizationComplete &&
    !bindingLoading &&
    !executionStatusLoading &&
    !diagnosticRunning &&
    !paidDiagnosticComplete;

  async function handleRunDiagnostic() {
    if (
      !executionBinding ||
      !canRunDiagnostic
    ) {
      return;
    }

    setDiagnosticRunning(
      true
    );

    setDiagnosticExecutionError(
      null
    );

    const authorizedAt =
      new Date().toISOString();

    const eventNonce =
      `${Date.now()}`;

    const contractExecutionEventId =
      `contract-${identity.assessmentId}-${eventNonce}`;

    const authorizationId =
      `paid-work-${identity.assessmentId}-${eventNonce}`;

    try {
      const response =
        await executePaidAssessment(
          config,
          {
            intake: {
              tenant_id:
                identity.tenantId,

              client_id:
                identity.clientId,

              engagement_id:
                identity.engagementId,

              assessment_id:
                identity.assessmentId,

              client_display_name:
                executionBinding
                  .client_display_name,

              assessment_name:
                executionBinding
                  .assessment_name,

              operator_name:
                executionAuthorization
                  .operatorName
                  .trim(),

              client_contact_name:
                executionAuthorization
                  .clientContactName
                  .trim(),

              assessment_scope_confirmed:
                executionAuthorization
                  .assessmentScopeConfirmed,

              evidence_scope_confirmed:
                executionAuthorization
                  .evidenceScopeConfirmed,

              client_data_use_confirmed:
                executionAuthorization
                  .clientDataUseConfirmed,

              operator_readiness_confirmed:
                executionAuthorization
                  .operatorReadinessConfirmed,

              evidence:
                executionBinding.evidence.map(
                  (item) => ({
                    evidence_id:
                      item.evidence_id,

                    source_kind:
                      item.source_kind,

                    description:
                      item.display_name,

                    classification:
                      executionAuthorization
                        .classification
                        .trim(),

                    client_authorized_for_assessment:
                      executionAuthorization
                        .clientAuthorizedForAssessment,

                    minimization_review_completed:
                      executionAuthorization
                        .minimizationReviewCompleted,

                    direct_identifiers_removed:
                      executionAuthorization
                        .directIdentifiersRemoved
                  })
                ),

              storage: {
                operator_controlled_location:
                  executionAuthorization
                    .operatorControlledLocation,

                access_restricted:
                  executionAuthorization
                    .accessRestricted,

                storage_protection_confirmed:
                  executionAuthorization
                    .storageProtectionConfirmed,

                backup_plan_recorded:
                  executionAuthorization
                    .backupPlanRecorded,

                retention_period_recorded:
                  executionAuthorization
                    .retentionPeriodRecorded,

                deletion_plan_recorded:
                  executionAuthorization
                    .deletionPlanRecorded
              }
            },

            contract_execution_event: {
              contract_execution_event_id:
                contractExecutionEventId,

              contract_executed:
                executionAuthorization
                  .contractExecuted,

              contract_execution_review_ready:
                executionAuthorization
                  .contractExecutionReviewReady,

              contract_execution_confirmed:
                executionAuthorization
                  .contractExecutionConfirmed,

              executed_contract_reference_recorded:
                executionAuthorization
                  .executedContractReferenceRecorded,

              executed_at_recorded:
                executionAuthorization
                  .executedAtRecorded,

              all_required_signatures_recorded:
                executionAuthorization
                  .allRequiredSignaturesRecorded,

              human_operator_confirmed_execution:
                executionAuthorization
                  .humanOperatorConfirmedExecution,

              requires_final_paid_work_authorization:
                true,

              human_boundary_required:
                true,

              gagf_kernel_authoritative:
                true,

              ai_override_allowed:
                false
            },

            paid_work_authorization: {
              authorization_id:
                authorizationId,

              tenant_id:
                identity.tenantId,

              client_id:
                identity.clientId,

              engagement_id:
                identity.engagementId,

              assessment_id:
                identity.assessmentId,

              contract_execution_event_id:
                contractExecutionEventId,

              authorized_by:
                config.actorId,

              authorized_at:
                authorizedAt,

              paid_assessment_authorized:
                executionAuthorization
                  .paidAssessmentAuthorized
            },

            execution_evidence_approvals:
              executionBinding.evidence.map(
                (item) => ({
                  evidence_id:
                    item.evidence_id,

                  approved_content_sha256:
                    item.content_sha256,

                  approved_by:
                    config.actorId,

                  approved_at:
                    authorizedAt,

                  execution_evidence_approved:
                    executionAuthorization
                      .executionEvidenceApproved
                })
              )
          }
        );

      setDiagnosticDisposition(
        response.result.disposition
      );

      await loadAssessment();

    } catch (caught) {
      if (
        caught instanceof
        GovernanceAssessmentApiError
      ) {
        setDiagnosticExecutionError(
          `Governed diagnostic execution failed with backend status ${caught.status}.`
        );
      } else {
        setDiagnosticExecutionError(
          "Governed diagnostic execution failed."
        );
      }
    } finally {
      setDiagnosticRunning(
        false
      );
    }
  }

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="assessments"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace" id="console-main-content" tabIndex={-1}>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Governance Assessment Results
            </p>
            <h1>
              {assessment?.assessment_name ??
                "Assessment"}
            </h1>
            <p className="page-description">
              {identity.clientId} /{" "}
              {identity.engagementId} /{" "}
              {identity.assessmentId}
            </p>
          </div>

          <div className="topbar-actions">
            <Link
              className="secondary-button button-link"
              href="/assessments"
            >
              Back to assessments
            </Link>

            <Link
              className="secondary-button button-link"
              href={
                "/evidence/"
                + encodeURIComponent(identity.tenantId)
                + "/"
                + encodeURIComponent(identity.clientId)
                + "/"
                + encodeURIComponent(identity.engagementId)
                + "/"
                + encodeURIComponent(identity.assessmentId)
              }
            >
              Explore evidence
            </Link>

            <Link
              className="secondary-button button-link"
              href={
                "/assessments/"
                + encodeURIComponent(identity.tenantId)
                + "/"
                + encodeURIComponent(identity.clientId)
                + "/"
                + encodeURIComponent(identity.engagementId)
                + "/"
                + encodeURIComponent(identity.assessmentId)
                + "/report"
              }
            >
              View client report
            </Link>

            <button
              className="refresh-button"
              type="button"
              disabled={loading}
              onClick={() =>
                void loadAssessment()
              }
            >
              {loading ? "Refreshing?" : "Refresh"}
            </button>
          </div>
        </header>

        {error && (
          <section
            className="error-panel"
            role="alert"
          >
            <div>
              <p className="error-title">
                Assessment unavailable
              </p>
              <p>{error}</p>
            </div>
          </section>
        )}

        {!error && loading && (
          <section className="detail-loading">
            <div className="loading-pulse" />
            <div className="loading-pulse" />
            <div className="loading-pulse" />
          </section>
        )}

        {!error &&
          !loading &&
          assessment &&
          summary &&
          artifacts && (
            <>
              <section className="assessment-result-status">
                <div>
                  <p className="status-heading">
                    Assessment status
                  </p>
                  <span className="status-badge status-healthy">
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />
                    {assessment.status}
                  </span>
                </div>

                <div>
                  <p className="status-heading">
                    Repository chain
                  </p>
                  <span
                    className={
                      summary.repository_chain_valid
                        ? "status-badge status-healthy"
                        : "status-badge status-warning"
                    }
                  >
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />
                    {summary.repository_chain_valid
                      ? "Verified"
                      : "Review required"}
                  </span>
                </div>

                <div>
                  <p className="status-heading">
                    Created
                  </p>
                  <p className="status-value">
                    {formatDate(
                      assessment.created_at
                    )}
                  </p>
                </div>
              </section>

              {bindingError && (
                <section
                  className="error-panel"
                  role="alert"
                >
                  <div>
                    <p className="error-title">
                      Paid execution unavailable
                    </p>

                    <p>
                      {bindingError}
                    </p>
                  </div>
                </section>
              )}

              {executionStatusError && (
                <section
                  className="error-panel"
                  role="alert"
                >
                  <div>
                    <p className="error-title">
                      Paid execution status unavailable
                    </p>

                    <p>
                      {executionStatusError}
                    </p>
                  </div>
                </section>
              )}

              {diagnosticExecutionError && (
                <section
                  className="error-panel"
                  role="alert"
                >
                  <div>
                    <p className="error-title">
                      Diagnostic execution failed
                    </p>

                    <p>
                      {diagnosticExecutionError}
                    </p>
                  </div>
                </section>
              )}

              <PaidAssessmentExecutionAuthorization
                binding={
                  executionBinding
                }
                value={
                  executionAuthorization
                }
                disabled={
                  bindingLoading ||
                  executionStatusLoading ||
                  diagnosticRunning ||
                  paidDiagnosticComplete
                }
                onChange={
                  setExecutionAuthorization
                }
              />

              <AssessmentWorkflowShell
                clientId={
                  identity.clientId
                }
                engagementId={
                  identity.engagementId
                }
                assessmentId={
                  identity.assessmentId
                }
                steps={
                  workflowSteps
                }
                evidenceHref={
                  evidenceHref
                }
                reportHref={
                  reportHref
                }
                canRunDiagnostic={
                  canRunDiagnostic
                }
                diagnosticRunning={
                  diagnosticRunning
                }
                diagnosticDisposition={
                  diagnosticDisposition
                }
                onRunDiagnostic={() =>
                  void handleRunDiagnostic()
                }
              />
              <section className="result-metrics-grid">
                <ResultMetric
                  label="Governance debt"
                  value={debtScore.toFixed(1)}
                  detail={`${debtBand} band`}
                />

                <ResultMetric
                  label="Evidence quality"
                  value={qualityScore.toFixed(2)}
                  detail={`${qualityGrade} quality`}
                />

                <ResultMetric
                  label="Weighted friction"
                  value={totalFriction.toFixed(1)}
                  detail="Governed constraint pressure"
                />

                <ResultMetric
                  label="Artifacts"
                  value={summary.artifact_count}
                  detail="Verified result records"
                />
              </section>

              <AssessmentReadinessPanel
  items={readinessItems}
/>

<AssessmentDeliveryStatus
  reportReady={
    clientReportReady
  }
  repositoryVerified={
    repositoryIntegrityReady
  }
  findingsReady={
    findingsReady
  }
  reportHref={
    reportHref
  }
/>

<AssessmentCloseoutPanel
  deliveryRecorded={false}
  reportId={
    clientReportArtifact?.artifact_id ??
    "Report package unavailable"
  }
  packageHash={
    clientReportArtifact?.artifact_hash ??
    "Package hash unavailable"
  }
/>

<DiagnosticFindingsSummary
  dominantConstraint={
    dominantConstraint
  }
  governanceDebtScore={
    debtScore
  }
  governanceDebtBand={
    debtBand
  }
  totalFriction={
    totalFriction
  }
  evidenceQualityScore={
    qualityScore
  }
  evidenceQualityGrade={
    qualityGrade
  }
  recognizedConstraintEvents={
    recognizedConstraintEvents
  }
  uniqueWorkItemCount={
    frictionUniqueWorkItemCount
  }
  findings={
    findings
  }
  readyForAnalysis={
    readyForAnalysis
  }
  evidenceHref={
    evidenceHref
  }
/>

<GovernanceFrictionMap
  items={frictionMapItems}
  totalFrictionScore={
    totalFriction
  }
  recognizedEventCount={
    recognizedConstraintEvents
  }
  uniqueWorkItemCount={
    frictionUniqueWorkItemCount
  }
  dominantConstraint={
    dominantConstraint
  }
  evidenceHref={
    evidenceHref
  }
/>

<GovernanceInterventionPlan
                items={interventionPlanItems}
                governanceDebtScore={
                  interventionGovernanceDebtScore
                }
                planHash={interventionPlanHash}
                schemaVersion={
                  interventionSchemaVersion
                }
              />

              <GovernanceRoadmap
                phases={governanceRoadmapPhases}
                totalItems={roadmapTotalItems}
                interventionPlanHash={
                  roadmapInterventionPlanHash
                }
                roadmapHash={roadmapHash}
                schemaVersion={
                  roadmapSchemaVersion
                }
              />

              <section className="detail-content-grid">
                <article className="panel executive-results-panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Executive interpretation
                    </p>
                    <h2>Assessment interpretation</h2>
                    </div>

                    <span
                      className={
                        readyForAnalysis
                          ? "status-badge status-healthy"
                          : "status-badge status-warning"
                      }
                    >
                      <span
                        className="status-dot"
                        aria-hidden="true"
                      />
                      {readyForAnalysis
                        ? "Evidence ready"
                        : "Evidence review"}
                    </span>
                  </div>

                  <p className="executive-summary">
                    {executiveSummary ??
                      "No executive summary was generated."}
                  </p>

                </article>

                <article className="panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Evidence constitution
                      </p>
                      <h2>Record identity</h2>
                    </div>
                  </div>

                  <dl className="connection-list">
                    <div>
                      <dt>Tenant</dt>
                      <dd>{assessment.tenant_id}</dd>
                    </div>
                    <div>
                      <dt>Client</dt>
                      <dd>{assessment.client_id}</dd>
                    </div>
                    <div>
                      <dt>Engagement</dt>
                      <dd>
                        {assessment.engagement_id}
                      </dd>
                    </div>
                    <div>
                      <dt>Assessment</dt>
                      <dd>
                        {assessment.assessment_id}
                      </dd>
                    </div>
                    <div>
                      <dt>Schema</dt>
                      <dd>
                        {assessment.schema_version}
                      </dd>
                    </div>
                  </dl>
                </article>
              </section>

              <section className="panel priorities-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Intervention plan
                    </p>
                    <h2>Priority actions</h2>
                  </div>

                  <span className="status-value">
                    {priorities.length} priorities
                  </span>
                </div>

                <div className="priority-list">
                  {priorities.map(
                    (priority, index) => (
                      <article
                        key={
                          textValue(
                            priority,
                            "intervention_id"
                          ) ?? String(index)
                        }
                        className="priority-item"
                      >
                        <span className="priority-rank">
                          {numberValue(
                            priority,
                            "rank"
                          ) ?? index + 1}
                        </span>

                        <div>
                          <h3>
                            {textValue(
                              priority,
                              "title"
                            ) ?? "Intervention"}
                          </h3>
                          <p>
                            {textValue(
                              priority,
                              "owner_role"
                            ) ?? "Unassigned owner"}
                            {" â€¢ "}
                            {textValue(
                              priority,
                              "target_horizon"
                            ) ?? "No horizon"}
                          </p>
                        </div>

                        <strong>
                          {(
                            numberValue(
                              priority,
                              "value_score"
                            ) ?? 0
                          ).toFixed(2)}
                        </strong>
                      </article>
                    )
                  )}
                </div>
              </section>

              <section className="panel artifacts-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Repository inventory
                    </p>
                    <h2>Governed artifact chain</h2>
                  </div>

                  <span className="status-value">
                    {artifacts.count} artifacts
                  </span>
                </div>

                <div className="artifact-table">
                  <div className="artifact-table-header">
                    <span>Sequence</span>
                    <span>Artifact type</span>
                    <span>Artifact ID</span>
                    <span>Chain</span>
                  </div>

                  {artifacts.items.map(
                    (artifact) => (
                      <div
                        className="artifact-table-row"
                        key={artifact.artifact_id}
                      >
                        <span>
                          {artifact.sequence_number}
                        </span>
                        <strong>
                          {artifact.artifact_type}
                        </strong>
                        <code>
                          {artifact.artifact_id}
                        </code>
                        <span className="status-badge status-healthy">
                          Verified
                        </span>
                      </div>
                    )
                  )}
                </div>
              </section>
            </>
          )}
      </section>
    </main>
  );
}
