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

type AssessmentWorkflowShellProps = {
  clientId: string;
  engagementId: string;
  assessmentId: string;
  steps: AssessmentWorkflowStep[];
  evidenceHref: string;
  reportHref: string;
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

export function AssessmentWorkflowShell({
  clientId,
  engagementId,
  assessmentId,
  steps,
  evidenceHref,
  reportHref
}: AssessmentWorkflowShellProps) {
  const completedCount = steps.filter(
    (step) => step.state === "complete"
  ).length;

  const allComplete =
    completedCount === steps.length;

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

      <div className="assessment-workflow-actions">
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