"use client";

import Link from "next/link";
import {
  useMemo,
  useState
} from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";
import {
  executeAssessment,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type AssessmentExecutionRequest,
  type AssessmentExecutionResponse
} from "@/lib/governance-assessment-api";

const DEFAULT_CSV = `event_id,event_type,occurred_at,work_item_id
event-001,APPROVAL_DELAYED,2026-01-01T12:00:00Z,TICKET-1
event-002,APPROVAL_DELAYED,2026-01-01T13:00:00Z,TICKET-2
event-003,WORK_BLOCKED,2026-01-02T12:00:00Z,TICKET-3
event-004,ESCALATION,2026-01-03T12:00:00Z,TICKET-4
`;

const INTAKE_STEPS = [
  {
    id: "client",
    label: "Client & Assessment",
    shortLabel: "Client",
    description:
      "Identify the customer engagement and governed assessment."
  },
  {
    id: "scope",
    label: "Assessment Scope",
    shortLabel: "Scope",
    description:
      "Define the workflows, organizations, period, and intended outcomes."
  },
  {
    id: "evidence",
    label: "Evidence",
    shortLabel: "Evidence",
    description:
      "Commit the required evidence source and provide the diagnostic data."
  },
  {
    id: "review",
    label: "Review & Execute",
    shortLabel: "Review",
    description:
      "Confirm the governed execution package before running FIP."
  }
] as const;

function splitLines(
  value: string
): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function executionErrorMessage(
  error: GovernanceAssessmentApiError
): string {
  if (
    typeof error.payload === "object" &&
    error.payload !== null &&
    "detail" in error.payload
  ) {
    const detail = (
      error.payload as {
        detail?: unknown;
      }
    ).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (
      typeof detail === "object" &&
      detail !== null &&
      "message" in detail &&
      typeof (
        detail as {
          message?: unknown;
        }
      ).message === "string"
    ) {
      return (
        detail as {
          message: string;
        }
      ).message;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (
            typeof item === "object" &&
            item !== null &&
            "msg" in item
          ) {
            return String(
              (
                item as {
                  msg: unknown;
                }
              ).msg
            );
          }

          return String(item);
        })
        .join("; ");
    }
  }

  return `Backend returned ${error.status}.`;
}

function evidenceRecordCount(
  csvText: string
): number {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  return Math.max(
    0,
    lines.length - 1
  );
}

export default function NewAssessmentPage() {
  const config = useMemo(
    () =>
      getGovernanceAssessmentApiConfig(),
    []
  );

  const [
    currentStep,
    setCurrentStep
  ] = useState(0);

  const [
    clientId,
    setClientId
  ] = useState("client-acme");

  const [
    clientDisplayName,
    setClientDisplayName
  ] = useState("ACME Corporation");

  const [
    engagementId,
    setEngagementId
  ] = useState("engagement-001");

  const [
    assessmentId,
    setAssessmentId
  ] = useState("assessment-001");

  const [
    assessmentName,
    setAssessmentName
  ] = useState(
    "Governance Runway Assessment"
  );

  const [
    workflowNames,
    setWorkflowNames
  ] = useState(
    "Incident Management"
  );

  const [
    organizationalUnits,
    setOrganizationalUnits
  ] = useState(
    "IT Operations"
  );

  const [
    periodStart,
    setPeriodStart
  ] = useState("2026-01-01");

  const [
    periodEnd,
    setPeriodEnd
  ] = useState("2026-06-30");

  const [
    objectives,
    setObjectives
  ] = useState(
    "Reduce governance friction"
  );

  const [
    expectedOutcomes,
    setExpectedOutcomes
  ] = useState(
    "Faster completion"
  );

  const [
    preparedBy,
    setPreparedBy
  ] = useState(
    "FIP Governance Services"
  );

  const [
    requirementId,
    setRequirementId
  ] = useState("required-csv");

  const [
    requirementDescription,
    setRequirementDescription
  ] = useState(
    "Workflow evidence"
  );

  const [
    minimumRecordCount,
    setMinimumRecordCount
  ] = useState(4);

  const [
    sourceId,
    setSourceId
  ] = useState("source-001");

  const [
    sourceDisplayName,
    setSourceDisplayName
  ] = useState(
    "Workflow Export"
  );

  const [
    csvText,
    setCsvText
  ] = useState(DEFAULT_CSV);

  const [
    maximumPriorities,
    setMaximumPriorities
  ] = useState(3);

  const [
    submitting,
    setSubmitting
  ] = useState(false);

  const [
    error,
    setError
  ] = useState<string | null>(
    null
  );

  const [
    result,
    setResult
  ] = useState<
    AssessmentExecutionResponse | null
  >(null);

  const [
    completedIdentity,
    setCompletedIdentity
  ] = useState<{
    tenantId: string;
    clientId: string;
    engagementId: string;
    assessmentId: string;
  } | null>(null);

  const workflowCount =
    splitLines(
      workflowNames
    ).length;

  const organizationalUnitCount =
    splitLines(
      organizationalUnits
    ).length;

  const objectiveCount =
    splitLines(
      objectives
    ).length;

  const expectedOutcomeCount =
    splitLines(
      expectedOutcomes
    ).length;

  const recordCount =
    evidenceRecordCount(
      csvText
    );

  const currentStepDefinition =
    INTAKE_STEPS[currentStep];

  const isFirstStep =
    currentStep === 0;

  const isFinalStep =
    currentStep ===
    INTAKE_STEPS.length - 1;

  function goToStep(
    index: number
  ) {
    if (
      index < 0 ||
      index >=
        INTAKE_STEPS.length ||
      submitting
    ) {
      return;
    }

    setCurrentStep(index);
    setError(null);
  }

  function goForward() {
    goToStep(
      Math.min(
        currentStep + 1,
        INTAKE_STEPS.length - 1
      )
    );
  }

  function goBackward() {
    goToStep(
      Math.max(
        currentStep - 1,
        0
      )
    );
  }

  async function submitAssessment(
    event:
      React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!isFinalStep) {
      goForward();
      return;
    }

    setSubmitting(true);
    setError(null);
    setResult(null);
    setCompletedIdentity(null);

    const request:
      AssessmentExecutionRequest = {
        tenant_id:
          config.tenantId,

        client_id:
          clientId.trim(),

        engagement_id:
          engagementId.trim(),

        assessment_id:
          assessmentId.trim(),

        assessment_name:
          assessmentName.trim(),

        workflow_names:
          splitLines(
            workflowNames
          ),

        organizational_units:
          splitLines(
            organizationalUnits
          ),

        period_start:
          periodStart,

        period_end:
          periodEnd,

        objectives:
          splitLines(
            objectives
          ),

        expected_outcomes:
          splitLines(
            expectedOutcomes
          ),

        evidence_requirements: [
          {
            requirement_id:
              requirementId.trim(),

            source_kind:
              "csv",

            description:
              requirementDescription.trim(),

            required:
              true,

            minimum_record_count:
              minimumRecordCount
          }
        ],

        evidence_inputs: [
          {
            source: {
              source_id:
                sourceId.trim(),

              kind:
                "csv",

              display_name:
                sourceDisplayName.trim()
            },

            csv_text:
              csvText
          }
        ],

        client_display_name:
          clientDisplayName.trim(),

        prepared_by:
          preparedBy.trim(),

        maximum_priorities:
          maximumPriorities
      };

    try {
      const executionResult =
        await executeAssessment(
          config,
          request
        );

      setResult(
        executionResult
      );

      setCompletedIdentity({
        tenantId:
          request.tenant_id,

        clientId:
          request.client_id,

        engagementId:
          request.engagement_id,

        assessmentId:
          request.assessment_id
      });
    } catch (caught) {
      if (
        caught instanceof
        GovernanceAssessmentApiError
      ) {
        setError(
          executionErrorMessage(
            caught
          )
        );
      } else {
        setError(
          "The Governance Assessment backend could not complete the request."
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  const completedAssessmentUrl =
    completedIdentity
      ? "/assessments/"
        + encodeURIComponent(
          completedIdentity.tenantId
        )
        + "/"
        + encodeURIComponent(
          completedIdentity.clientId
        )
        + "/"
        + encodeURIComponent(
          completedIdentity.engagementId
        )
        + "/"
        + encodeURIComponent(
          completedIdentity.assessmentId
        )
      : null;

  const completedReportUrl =
    completedAssessmentUrl
      ? `${completedAssessmentUrl}/report`
      : null;

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="assessments"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section
        className="workspace"
        id="console-main-content"
        tabIndex={-1}
      >
        <header className="topbar">
          <div>
            <p className="eyebrow">
              FIP Operator Workspace
            </p>

            <h1>
              New Governance Assessment
            </h1>

            <p className="page-description">
              Build a governed diagnostic
              package through a guided intake,
              review the evidence commitment,
              and execute FIP against the real
              assessment backend.
            </p>
          </div>

          <Link
            className="secondary-button button-link"
            href="/assessments"
          >
            Back to assessments
          </Link>
        </header>

        <section
          className="assessment-intake-overview"
          aria-labelledby="assessment-intake-title"
        >
          <div>
            <p className="panel-kicker">
              Guided assessment intake
            </p>

            <h2
              id="assessment-intake-title"
            >
              Prepare the diagnostic package
            </h2>

            <p>
              Complete the commercial context,
              scope, and evidence commitment
              before FIP executes the governed
              diagnostic.
            </p>
          </div>

          <div className="assessment-intake-position">
            <span>
              Step {currentStep + 1} of{" "}
              {INTAKE_STEPS.length}
            </span>

            <strong>
              {
                currentStepDefinition.label
              }
            </strong>
          </div>
        </section>

        <nav
          className="assessment-intake-stepper"
          aria-label="Assessment intake steps"
        >
          <ol>
            {INTAKE_STEPS.map(
              (
                step,
                index
              ) => {
                const state =
                  index < currentStep
                    ? "complete"
                    : index ===
                        currentStep
                      ? "current"
                      : "upcoming";

                const stateLabel =
                  state === "complete"
                    ? "Complete"
                    : state ===
                        "current"
                      ? "Current"
                      : "Upcoming";

                return (
                  <li
                    key={step.id}
                    className={
                      "assessment-intake-step "
                      + `assessment-intake-step-${state}`
                    }
                  >
                    <button
                      type="button"
                      onClick={() =>
                        goToStep(
                          index
                        )
                      }
                      aria-current={
                        index ===
                        currentStep
                          ? "step"
                          : undefined
                      }
                      aria-label={
                        step.shortLabel
                        + " "
                        + stateLabel
                      }
                    >
                      <span
                        className="assessment-intake-step-number"
                        aria-hidden="true"
                      >
                        {index + 1}
                      </span>

                      <span className="assessment-intake-step-copy">
                        <strong>
                          {
                            step.shortLabel
                          }
                        </strong>

                        <small>
                          {stateLabel}
                        </small>
                      </span>
                    </button>
                  </li>
                );
              }
            )}
          </ol>
        </nav>

        {error && (
          <section
            className="error-panel"
            role="alert"
          >
            <div>
              <p className="error-title">
                Execution failed
              </p>

              <p>{error}</p>
            </div>
          </section>
        )}

        {result && (
  <section
    className="execution-success governed-execution-receipt"
    aria-live="polite"
    aria-labelledby="governed-execution-receipt-title"
  >
    <header className="governed-execution-receipt-header">
      <div>
        <p className="panel-kicker">
          Governed execution receipt
        </p>

        <h2 id="governed-execution-receipt-title">
          Assessment execution complete
        </h2>

        <p>
          FIP completed the governed assessment,
          persisted the resulting artifacts, and
          returned the cryptographic bindings for
          this execution.
        </p>
      </div>

      <span className="status-badge status-healthy">
        <span
          className="status-dot"
          aria-hidden="true"
        />

        Execution verified
      </span>
    </header>

    <div className="governed-execution-checks">
      <article>
        <span
          className="governed-execution-check"
          aria-hidden="true"
        >
          ✓
        </span>

        <div>
          <strong>Request bound</strong>
          <p>
            The submitted assessment package was
            canonicalized and hashed before
            execution.
          </p>
        </div>
      </article>

      <article>
        <span
          className="governed-execution-check"
          aria-hidden="true"
        >
          ✓
        </span>

        <div>
          <strong>Assessment executed</strong>
          <p>
            The governed assessment pipeline
            completed successfully.
          </p>
        </div>
      </article>

      <article>
        <span
          className="governed-execution-check"
          aria-hidden="true"
        >
          ✓
        </span>

        <div>
          <strong>Persistence bound</strong>
          <p>
            The persisted result references the
            exact executed demonstration.
          </p>
        </div>
      </article>

      <article>
        <span
          className="governed-execution-check"
          aria-hidden="true"
        >
          ✓
        </span>

        <div>
          <strong>Report generated</strong>
          <p>
            The execution produced a governed
            report package for this assessment.
          </p>
        </div>
      </article>
    </div>

    <div className="governed-execution-summary">
      <article>
        <span>Hierarchy</span>
        <strong>{result.hierarchy_key}</strong>
      </article>

      <article>
        <span>Governed artifacts</span>
        <strong>{result.artifact_count}</strong>
      </article>

      <article>
        <span>Report ID</span>
        <strong>{result.report_id}</strong>
      </article>

      {result.schema_version && (
        <article>
          <span>Receipt schema</span>
          <strong>{result.schema_version}</strong>
        </article>
      )}
    </div>

    <div className="governed-execution-provenance">
      <div className="governed-execution-provenance-heading">
        <div>
          <p className="panel-kicker">
            Cryptographic provenance
          </p>

          <h3>Execution bindings</h3>
        </div>

        <p>
          These hashes bind the submitted request,
          executed assessment, persisted result,
          and final application receipt.
        </p>
      </div>

      <dl className="governed-execution-hashes">
        <div>
          <dt>Request hash</dt>
          <dd>
            <code>{result.request_hash}</code>
          </dd>
        </div>

        <div>
          <dt>Demonstration hash</dt>
          <dd>
            <code>{result.demonstration_hash}</code>
          </dd>
        </div>

        <div>
          <dt>Persistence hash</dt>
          <dd>
            <code>{result.persistence_hash}</code>
          </dd>
        </div>

        <div>
          <dt>Application hash</dt>
          <dd>
            <code>{result.application_hash}</code>
          </dd>
        </div>
      </dl>
    </div>

    <aside className="governed-execution-integrity-boundary">
      <div>
        <strong>Execution integrity established</strong>

        <p>
          Repository-chain integrity is verified
          separately when the persisted assessment
          workspace loads.
        </p>
      </div>

      <span>
        Next: repository verification
      </span>
    </aside>

    <div className="execution-success-actions governed-execution-actions">
      {completedAssessmentUrl && (
        <Link
          className="refresh-button button-link"
          href={completedAssessmentUrl}
        >
          Open assessment
        </Link>
      )}

      {completedReportUrl && (
        <Link
          className="secondary-button button-link"
          href={completedReportUrl}
        >
          View client report
        </Link>
      )}

      <Link
        className="secondary-button button-link"
        href="/assessments"
      >
        View all assessments
      </Link>
    </div>
  </section>
)}

        <form
          className="execution-form assessment-guided-form"
          onSubmit={submitAssessment}
        >
          <section className="assessment-guided-stage">
            <header className="assessment-guided-stage-header">
              <div>
                <p className="panel-kicker">
                  Step {currentStep + 1}
                </p>

                <h2>
                  {currentStepDefinition.label}
                </h2>

                <p>
                  {
                    currentStepDefinition.description
                  }
                </p>
              </div>

              <span className="assessment-guided-stage-badge">
                {currentStep + 1}/
                {INTAKE_STEPS.length}
              </span>
            </header>

            {currentStep === 0 && (
              <div className="form-section assessment-guided-section">
                <div className="form-section-heading">
                  <p className="panel-kicker">
                    Commercial hierarchy
                  </p>

                  <h2>
                    Who is this assessment
                    for?
                  </h2>

                  <p>
                    Establish the governed
                    tenant, client,
                    engagement, and
                    assessment identity
                    used throughout the
                    evidence and report
                    chain.
                  </p>
                </div>

                <div className="form-grid">
                  <label>
                    <span>
                      Tenant ID
                    </span>

                    <input
                      value={config.tenantId}
                      disabled
                    />
                  </label>

                  <label>
                    <span>
                      Client ID
                    </span>

                    <input
                      required
                      value={clientId}
                      onChange={(
                        event
                      ) =>
                        setClientId(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Client display name
                    </span>

                    <input
                      required
                      value={
                        clientDisplayName
                      }
                      onChange={(
                        event
                      ) =>
                        setClientDisplayName(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Engagement ID
                    </span>

                    <input
                      required
                      value={engagementId}
                      onChange={(
                        event
                      ) =>
                        setEngagementId(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Assessment ID
                    </span>

                    <input
                      required
                      value={assessmentId}
                      onChange={(
                        event
                      ) =>
                        setAssessmentId(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Assessment name
                    </span>

                    <input
                      required
                      value={
                        assessmentName
                      }
                      onChange={(
                        event
                      ) =>
                        setAssessmentName(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>
                </div>
              </div>
            )}

            {currentStep === 1 && (
              <div className="form-section assessment-guided-section">
                <div className="form-section-heading">
                  <p className="panel-kicker">
                    Assessment scope
                  </p>

                  <h2>
                    What should FIP examine?
                  </h2>

                  <p>
                    Define the operating
                    period, workflows,
                    organizational
                    boundaries, objectives,
                    and expected outcomes.
                    Enter one item per line
                    in multi-value fields.
                  </p>
                </div>

                <div className="form-grid">
                  <label>
                    <span>
                      Period start
                    </span>

                    <input
                      type="date"
                      required
                      value={
                        periodStart
                      }
                      onChange={(
                        event
                      ) =>
                        setPeriodStart(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Period end
                    </span>

                    <input
                      type="date"
                      required
                      value={periodEnd}
                      onChange={(
                        event
                      ) =>
                        setPeriodEnd(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label className="form-span-full">
                    <span>
                      Workflow names
                    </span>

                    <textarea
                      required
                      rows={3}
                      value={
                        workflowNames
                      }
                      onChange={(
                        event
                      ) =>
                        setWorkflowNames(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label className="form-span-full">
                    <span>
                      Organizational units
                    </span>

                    <textarea
                      required
                      rows={3}
                      value={
                        organizationalUnits
                      }
                      onChange={(
                        event
                      ) =>
                        setOrganizationalUnits(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label className="form-span-full">
                    <span>
                      Objectives
                    </span>

                    <textarea
                      required
                      rows={3}
                      value={objectives}
                      onChange={(
                        event
                      ) =>
                        setObjectives(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label className="form-span-full">
                    <span>
                      Expected outcomes
                    </span>

                    <textarea
                      required
                      rows={3}
                      value={
                        expectedOutcomes
                      }
                      onChange={(
                        event
                      ) =>
                        setExpectedOutcomes(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="form-section assessment-guided-section">
                <div className="form-section-heading">
                  <p className="panel-kicker">
                    Evidence commitment
                  </p>

                  <h2>
                    What evidence will
                    support the diagnostic?
                  </h2>

                  <p>
                    Define the required CSV
                    commitment and provide
                    the evidence payload
                    that will enter the
                    governed intake
                    pipeline.
                  </p>
                </div>

                <div className="assessment-evidence-summary">
                  <div>
                    <span>
                      Current evidence
                      records
                    </span>

                    <strong>
                      {recordCount}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Required minimum
                    </span>

                    <strong>
                      {
                        minimumRecordCount
                      }
                    </strong>
                  </div>

                  <div>
                    <span>
                      Admission status
                    </span>

                    <strong>
                      {recordCount >=
                      minimumRecordCount
                        ? "Count satisfied"
                        : "More records needed"}
                    </strong>
                  </div>
                </div>

                <div className="form-grid">
                  <label>
                    <span>
                      Requirement ID
                    </span>

                    <input
                      required
                      value={
                        requirementId
                      }
                      onChange={(
                        event
                      ) =>
                        setRequirementId(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Minimum record count
                    </span>

                    <input
                      type="number"
                      required
                      min={1}
                      value={
                        minimumRecordCount
                      }
                      onChange={(
                        event
                      ) =>
                        setMinimumRecordCount(
                          Number(
                            event.target
                              .value
                          )
                        )
                      }
                    />
                  </label>

                  <label className="form-span-full">
                    <span>
                      Requirement description
                    </span>

                    <input
                      required
                      value={
                        requirementDescription
                      }
                      onChange={(
                        event
                      ) =>
                        setRequirementDescription(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Source ID
                    </span>

                    <input
                      required
                      value={sourceId}
                      onChange={(
                        event
                      ) =>
                        setSourceId(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label>
                    <span>
                      Source display name
                    </span>

                    <input
                      required
                      value={
                        sourceDisplayName
                      }
                      onChange={(
                        event
                      ) =>
                        setSourceDisplayName(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>

                  <label className="form-span-full">
                    <span>
                      CSV evidence
                    </span>

                    <textarea
                      className="csv-editor"
                      required
                      rows={14}
                      spellCheck={false}
                      value={csvText}
                      onChange={(
                        event
                      ) =>
                        setCsvText(
                          event.target
                            .value
                        )
                      }
                    />
                  </label>
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="assessment-review-layout">
                <section className="assessment-review-card">
                  <div className="assessment-review-card-heading">
                    <p className="panel-kicker">
                      Commercial identity
                    </p>

                    <h3>
                      Client & assessment
                    </h3>
                  </div>

                  <dl className="assessment-review-list">
                    <div>
                      <dt>Tenant</dt>
                      <dd>
                        {config.tenantId}
                      </dd>
                    </div>

                    <div>
                      <dt>Client</dt>
                      <dd>
                        {
                          clientDisplayName
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Client ID</dt>
                      <dd>
                        {clientId}
                      </dd>
                    </div>

                    <div>
                      <dt>Engagement</dt>
                      <dd>
                        {engagementId}
                      </dd>
                    </div>

                    <div>
                      <dt>Assessment</dt>
                      <dd>
                        {assessmentName}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Assessment ID
                      </dt>
                      <dd>
                        {assessmentId}
                      </dd>
                    </div>
                  </dl>

                  <button
                    className="assessment-review-edit"
                    type="button"
                    onClick={() =>
                      goToStep(0)
                    }
                  >
                    Edit client details
                  </button>
                </section>

                <section className="assessment-review-card">
                  <div className="assessment-review-card-heading">
                    <p className="panel-kicker">
                      Diagnostic scope
                    </p>

                    <h3>
                      Scope summary
                    </h3>
                  </div>

                  <dl className="assessment-review-list">
                    <div>
                      <dt>Period</dt>
                      <dd>
                        {periodStart} to{" "}
                        {periodEnd}
                      </dd>
                    </div>

                    <div>
                      <dt>Workflows</dt>
                      <dd>
                        {workflowCount}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Organizational units
                      </dt>
                      <dd>
                        {
                          organizationalUnitCount
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Objectives</dt>
                      <dd>
                        {objectiveCount}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Expected outcomes
                      </dt>
                      <dd>
                        {
                          expectedOutcomeCount
                        }
                      </dd>
                    </div>
                  </dl>

                  <button
                    className="assessment-review-edit"
                    type="button"
                    onClick={() =>
                      goToStep(1)
                    }
                  >
                    Edit scope
                  </button>
                </section>

                <section className="assessment-review-card">
                  <div className="assessment-review-card-heading">
                    <p className="panel-kicker">
                      Evidence
                    </p>

                    <h3>
                      Evidence commitment
                    </h3>
                  </div>

                  <dl className="assessment-review-list">
                    <div>
                      <dt>Source</dt>
                      <dd>
                        {
                          sourceDisplayName
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Source ID</dt>
                      <dd>
                        {sourceId}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Evidence records
                      </dt>
                      <dd>
                        {recordCount}
                      </dd>
                    </div>

                    <div>
                      <dt>
                        Required minimum
                      </dt>
                      <dd>
                        {
                          minimumRecordCount
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Requirement</dt>
                      <dd>
                        {
                          requirementDescription
                        }
                      </dd>
                    </div>
                  </dl>

                  <button
                    className="assessment-review-edit"
                    type="button"
                    onClick={() =>
                      goToStep(2)
                    }
                  >
                    Edit evidence
                  </button>
                </section>

                <section className="assessment-review-card assessment-review-delivery">
                  <div className="assessment-review-card-heading">
                    <p className="panel-kicker">
                      Delivery
                    </p>

                    <h3>
                      Report preparation
                    </h3>

                    <p>
                      Configure how the
                      governed assessment
                      package will be
                      prepared for operator
                      review.
                    </p>
                  </div>

                  <div className="form-grid">
                    <label>
                      <span>
                        Prepared by
                      </span>

                      <input
                        required
                        value={
                          preparedBy
                        }
                        onChange={(
                          event
                        ) =>
                          setPreparedBy(
                            event.target
                              .value
                          )
                        }
                      />
                    </label>

                    <label>
                      <span>
                        Maximum priorities
                      </span>

                      <input
                        type="number"
                        min={1}
                        max={10}
                        value={
                          maximumPriorities
                        }
                        onChange={(
                          event
                        ) =>
                          setMaximumPriorities(
                            Number(
                              event.target
                                .value
                            )
                          )
                        }
                      />
                    </label>
                  </div>
                </section>

                <section className="assessment-execution-gate">
                  <div>
                    <p className="panel-kicker">
                      Governed execution
                      gate
                    </p>

                    <h3>
                      Ready to run FIP
                    </h3>

                    <p>
                      Execution will submit
                      this package to the
                      real Governance
                      Assessment backend.
                      The resulting
                      assessment identity
                      and persisted
                      artifacts remain
                      authoritative.
                    </p>
                  </div>

                  <div className="assessment-execution-gate-status">
                    <span className="status-badge status-healthy">
                      <span
                        className="status-dot"
                        aria-hidden="true"
                      />

                      Package prepared
                    </span>

                    <strong>
                      {recordCount} evidence
                      records
                    </strong>
                  </div>
                </section>
              </div>
            )}
          </section>

          <div className="assessment-guided-actions">
            <div>
              {isFirstStep ? (
                <Link
                  className="secondary-button button-link"
                  href="/assessments"
                >
                  Cancel
                </Link>
              ) : (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={
                    goBackward
                  }
                  disabled={
                    submitting
                  }
                >
                  Back
                </button>
              )}
            </div>

            <div className="assessment-guided-actions-primary">
              {!isFinalStep && (
                <button
                  className="refresh-button"
                  type="button"
                  onClick={
                    goForward
                  }
                  disabled={
                    submitting
                  }
                >
                  {currentStep === 0
                    ? "Continue to scope"
                    : currentStep === 1
                      ? "Continue to evidence"
                      : "Review assessment"}
                </button>
              )}

              {isFinalStep && (
                <button
                  className="refresh-button"
                  type="submit"
                  disabled={
                    submitting
                  }
                >
                  {submitting
                    ? "Executing assessment..."
                    : "Execute assessment"}
                </button>
              )}
            </div>
          </div>
        </form>
      </section>
    </main>
  );
}