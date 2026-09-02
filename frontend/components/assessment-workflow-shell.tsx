"use client";

import Link from "next/link";

export type AssessmentWorkflowStepState =
  | "complete"
  | "current"
  | "upcoming";

export type AssessmentWorkflowStep = {
  id: string;
  label: string;
  description: string;
  state: AssessmentWorkflowStepState;
};

export type AssessmentDiagnosticDisposition =
  | "executed"
  | "resumed"
  | "reconciled";

type AssessmentWorkflowShellProps = {
  clientId: string;
  engagementId: string;
  assessmentId: string;
  steps: AssessmentWorkflowStep[];
  evidenceHref: string;
  reportHref: string;

  canRunDiagnostic?: boolean;
  diagnosticRunning?: boolean;
  diagnosticDisposition?:
    AssessmentDiagnosticDisposition | null;
  onRunDiagnostic?: () => void;
};

function stateLabel(
  state: AssessmentWorkflowStepState
): string {
  if (state === "complete") {
    return "Complete";
  }

  if (state === "current") {
    return "Current";
  }

  return "Upcoming";
}

function dispositionLabel(
  disposition:
    AssessmentDiagnosticDisposition
): string {
  if (disposition === "executed") {
    return "Diagnostic executed";
  }

  if (disposition === "resumed") {
    return "Diagnostic resumed";
  }

  return "Diagnostic reconciled";
}

export function AssessmentWorkflowShell({
  clientId,
  engagementId,
  assessmentId,
  steps,
  evidenceHref,
  reportHref,
  canRunDiagnostic = false,
  diagnosticRunning = false,
  diagnosticDisposition = null,
  onRunDiagnostic
}: AssessmentWorkflowShellProps) {
  const completedCount = steps.filter(
    (step) => step.state === "complete"
  ).length;

  const allComplete =
    completedCount === steps.length;

  const diagnosticStep =
    steps.find(
      (step) =>
        step.id === "diagnostic"
    );

  const diagnosticComplete =
    diagnosticStep?.state === "complete";

  const diagnosticActionEnabled =
    canRunDiagnostic &&
    !diagnosticRunning &&
    !diagnosticComplete &&
    typeof onRunDiagnostic === "function";

  return (
    <section
      className="assessment-workflow-shell"
      aria-labelledby="assessment-workflow-title"
    >
      <div className="assessment-workflow-header">
        <div>
          <p className="panel-kicker">
            Operator diagnostic workspace
          </p>

          <h2 id="assessment-workflow-title">
            Assessment workflow
          </h2>

          <p className="assessment-workflow-description">
            Follow the governed path from evidence
            intake through customer-ready reporting.
          </p>
        </div>

        <span
          className={
            allComplete
              ? "status-badge status-healthy"
              : "status-badge status-warning"
          }
        >
          <span
            className="status-dot"
            aria-hidden="true"
          />

          {allComplete
            ? "Workflow complete"
            : "Workflow in progress"}
        </span>
      </div>

      <dl className="assessment-workflow-identity">
        <div>
          <dt>Client</dt>
          <dd>{clientId}</dd>
        </div>

        <div>
          <dt>Engagement</dt>
          <dd>{engagementId}</dd>
        </div>

        <div>
          <dt>Assessment</dt>
          <dd>{assessmentId}</dd>
        </div>
      </dl>

      <ol
        className="assessment-workflow-steps"
        aria-label="Assessment workflow progress"
      >
        {steps.map((step, index) => (
          <li
            className={
              "assessment-workflow-step "
              + `assessment-workflow-step-${step.state}`
            }
            key={step.id}
            aria-current={
              step.state === "current"
                ? "step"
                : undefined
            }
          >
            <span
              className="assessment-workflow-step-number"
              aria-hidden="true"
            >
              {index + 1}
            </span>

            <div className="assessment-workflow-step-copy">
              <div className="assessment-workflow-step-heading">
                <h3>{step.label}</h3>

                <span
                  className={
                    "assessment-workflow-state "
                    + `assessment-workflow-state-${step.state}`
                  }
                >
                  {stateLabel(step.state)}
                </span>
              </div>

              <p>{step.description}</p>
            </div>
          </li>
        ))}
      </ol>

      {diagnosticDisposition && (
        <div
          className="assessment-workflow-diagnostic-status"
          role="status"
        >
          <span
            className="status-badge status-healthy"
          >
            <span
              className="status-dot"
              aria-hidden="true"
            />

            {dispositionLabel(
              diagnosticDisposition
            )}
          </span>
        </div>
      )}

      <div className="assessment-workflow-actions">
        <button
          className="refresh-button"
          type="button"
          disabled={
            !diagnosticActionEnabled
          }
          onClick={
            diagnosticActionEnabled
              ? onRunDiagnostic
              : undefined
          }
        >
          {diagnosticRunning
            ? "Running diagnostic..."
            : diagnosticComplete
              ? "Diagnostic complete"
              : "Run Diagnostic"}
        </button>

        <Link
          className="secondary-button button-link"
          href={evidenceHref}
        >
          Explore evidence
        </Link>

        <Link
          className="refresh-button button-link"
          href={reportHref}
        >
          Open client report
        </Link>
      </div>
    </section>
  );
}