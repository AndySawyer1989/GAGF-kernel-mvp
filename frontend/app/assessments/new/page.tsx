"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

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

function splitLines(value: string): string[] {
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
        detail as { message?: unknown }
      ).message === "string"
    ) {
      return (
        detail as { message: string }
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
              (item as { msg: unknown }).msg
            );
          }

          return String(item);
        })
        .join("; ");
    }
  }

  return `Backend returned ${error.status}.`;
}

export default function NewAssessmentPage() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [clientId, setClientId] =
    useState("client-acme");
  const [clientDisplayName, setClientDisplayName] =
    useState("ACME Corporation");
  const [engagementId, setEngagementId] =
    useState("engagement-001");
  const [assessmentId, setAssessmentId] =
    useState("assessment-001");
  const [assessmentName, setAssessmentName] =
    useState("Governance Runway Assessment");
  const [workflowNames, setWorkflowNames] =
    useState("Incident Management");
  const [organizationalUnits, setOrganizationalUnits] =
    useState("IT Operations");
  const [periodStart, setPeriodStart] =
    useState("2026-01-01");
  const [periodEnd, setPeriodEnd] =
    useState("2026-06-30");
  const [objectives, setObjectives] =
    useState("Reduce governance friction");
  const [expectedOutcomes, setExpectedOutcomes] =
    useState("Faster completion");
  const [preparedBy, setPreparedBy] =
    useState("FIP Governance Services");
  const [requirementId, setRequirementId] =
    useState("required-csv");
  const [requirementDescription, setRequirementDescription] =
    useState("Workflow evidence");
  const [minimumRecordCount, setMinimumRecordCount] =
    useState(4);
  const [sourceId, setSourceId] =
    useState("source-001");
  const [sourceDisplayName, setSourceDisplayName] =
    useState("Workflow Export");
  const [csvText, setCsvText] =
    useState(DEFAULT_CSV);
  const [maximumPriorities, setMaximumPriorities] =
    useState(3);

  const [submitting, setSubmitting] =
    useState(false);
  const [error, setError] =
    useState<string | null>(null);
  const [result, setResult] =
    useState<AssessmentExecutionResponse | null>(
      null
    );

  const [completedIdentity, setCompletedIdentity] =
    useState<{
      tenantId: string;
      clientId: string;
      engagementId: string;
      assessmentId: string;
    } | null>(null);

  async function submitAssessment(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setSubmitting(true);
    setError(null);
    setResult(null);
    setCompletedIdentity(null);

    const request: AssessmentExecutionRequest = {
      tenant_id: config.tenantId,
      client_id: clientId.trim(),
      engagement_id: engagementId.trim(),
      assessment_id: assessmentId.trim(),
      assessment_name: assessmentName.trim(),
      workflow_names: splitLines(workflowNames),
      organizational_units:
        splitLines(organizationalUnits),
      period_start: periodStart,
      period_end: periodEnd,
      objectives: splitLines(objectives),
      expected_outcomes:
        splitLines(expectedOutcomes),
      evidence_requirements: [
        {
          requirement_id: requirementId.trim(),
          source_kind: "csv",
          description:
            requirementDescription.trim(),
          required: true,
          minimum_record_count:
            minimumRecordCount
        }
      ],
      evidence_inputs: [
        {
          source: {
            source_id: sourceId.trim(),
            kind: "csv",
            display_name:
              sourceDisplayName.trim()
          },
          csv_text: csvText
        }
      ],
      client_display_name:
        clientDisplayName.trim(),
      prepared_by: preparedBy.trim(),
      maximum_priorities: maximumPriorities
    };

    try {
      const executionResult =
        await executeAssessment(
          config,
          request
        );

      setResult(executionResult);

      setCompletedIdentity({
        tenantId: request.tenant_id,
        clientId: request.client_id,
        engagementId: request.engagement_id,
        assessmentId: request.assessment_id
      });
    } catch (caught) {
      if (
        caught instanceof GovernanceAssessmentApiError
      ) {
        setError(
          executionErrorMessage(caught)
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

      <section className="workspace" id="console-main-content" tabIndex={-1}>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Governance Assessment
            </p>
            <h1>Execute Assessment</h1>
            <p className="page-description">
              Define commercial context, assessment
              scope, evidence commitments, and CSV
              evidence for deterministic execution.
            </p>
          </div>

          <Link
            className="secondary-button button-link"
            href="/assessments"
          >
            Back to assessments
          </Link>
        </header>

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
            className="execution-success"
            aria-live="polite"
          >
            <div>
              <p className="panel-kicker">
                Assessment complete
              </p>
              <h2>{result.hierarchy_key}</h2>
              <p>
                {result.artifact_count} governed
                artifacts were persisted.
              </p>
            </div>

            <div className="execution-success-actions">
              <span className="status-badge status-healthy">
                <span
                  className="status-dot"
                  aria-hidden="true"
                />
                Execution verified
              </span>

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
          className="execution-form"
          onSubmit={submitAssessment}
        >
          <section className="form-section">
            <div className="form-section-heading">
              <p className="panel-kicker">
                Commercial hierarchy
              </p>
              <h2>
                Tenant, client, engagement, assessment
              </h2>
            </div>

            <div className="form-grid">
              <label>
                <span>Tenant ID</span>
                <input
                  value={config.tenantId}
                  disabled
                />
              </label>

              <label>
                <span>Client ID</span>
                <input
                  required
                  value={clientId}
                  onChange={(event) =>
                    setClientId(event.target.value)
                  }
                />
              </label>

              <label>
                <span>Client display name</span>
                <input
                  required
                  value={clientDisplayName}
                  onChange={(event) =>
                    setClientDisplayName(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Engagement ID</span>
                <input
                  required
                  value={engagementId}
                  onChange={(event) =>
                    setEngagementId(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Assessment ID</span>
                <input
                  required
                  value={assessmentId}
                  onChange={(event) =>
                    setAssessmentId(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Assessment name</span>
                <input
                  required
                  value={assessmentName}
                  onChange={(event) =>
                    setAssessmentName(
                      event.target.value
                    )
                  }
                />
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <p className="panel-kicker">
                Assessment scope
              </p>
              <h2>
                Workflows, units, and objectives
              </h2>
              <p>
                Enter one item per line in multi-value
                fields.
              </p>
            </div>

            <div className="form-grid">
              <label>
                <span>Period start</span>
                <input
                  type="date"
                  required
                  value={periodStart}
                  onChange={(event) =>
                    setPeriodStart(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Period end</span>
                <input
                  type="date"
                  required
                  value={periodEnd}
                  onChange={(event) =>
                    setPeriodEnd(
                      event.target.value
                    )
                  }
                />
              </label>

              <label className="form-span-full">
                <span>Workflow names</span>
                <textarea
                  required
                  rows={3}
                  value={workflowNames}
                  onChange={(event) =>
                    setWorkflowNames(
                      event.target.value
                    )
                  }
                />
              </label>

              <label className="form-span-full">
                <span>Organizational units</span>
                <textarea
                  required
                  rows={3}
                  value={organizationalUnits}
                  onChange={(event) =>
                    setOrganizationalUnits(
                      event.target.value
                    )
                  }
                />
              </label>

              <label className="form-span-full">
                <span>Objectives</span>
                <textarea
                  required
                  rows={3}
                  value={objectives}
                  onChange={(event) =>
                    setObjectives(
                      event.target.value
                    )
                  }
                />
              </label>

              <label className="form-span-full">
                <span>Expected outcomes</span>
                <textarea
                  required
                  rows={3}
                  value={expectedOutcomes}
                  onChange={(event) =>
                    setExpectedOutcomes(
                      event.target.value
                    )
                  }
                />
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <p className="panel-kicker">
                Evidence commitment
              </p>
              <h2>
                Required CSV source
              </h2>
            </div>

            <div className="form-grid">
              <label>
                <span>Requirement ID</span>
                <input
                  required
                  value={requirementId}
                  onChange={(event) =>
                    setRequirementId(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Minimum record count</span>
                <input
                  type="number"
                  required
                  min={1}
                  value={minimumRecordCount}
                  onChange={(event) =>
                    setMinimumRecordCount(
                      Number(event.target.value)
                    )
                  }
                />
              </label>

              <label className="form-span-full">
                <span>Requirement description</span>
                <input
                  required
                  value={requirementDescription}
                  onChange={(event) =>
                    setRequirementDescription(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Source ID</span>
                <input
                  required
                  value={sourceId}
                  onChange={(event) =>
                    setSourceId(event.target.value)
                  }
                />
              </label>

              <label>
                <span>Source display name</span>
                <input
                  required
                  value={sourceDisplayName}
                  onChange={(event) =>
                    setSourceDisplayName(
                      event.target.value
                    )
                  }
                />
              </label>

              <label className="form-span-full">
                <span>CSV evidence</span>
                <textarea
                  className="csv-editor"
                  required
                  rows={12}
                  spellCheck={false}
                  value={csvText}
                  onChange={(event) =>
                    setCsvText(event.target.value)
                  }
                />
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section-heading">
              <p className="panel-kicker">
                Delivery
              </p>
              <h2>
                Report preparation
              </h2>
            </div>

            <div className="form-grid">
              <label>
                <span>Prepared by</span>
                <input
                  required
                  value={preparedBy}
                  onChange={(event) =>
                    setPreparedBy(
                      event.target.value
                    )
                  }
                />
              </label>

              <label>
                <span>Maximum priorities</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={maximumPriorities}
                  onChange={(event) =>
                    setMaximumPriorities(
                      Number(event.target.value)
                    )
                  }
                />
              </label>
            </div>
          </section>

          <div className="execution-actions">
            <Link
              className="secondary-button button-link"
              href="/assessments"
            >
              Cancel
            </Link>

            <button
              className="refresh-button"
              type="submit"
              disabled={submitting}
            >
              {submitting
                ? "Executing assessment?"
                : "Execute assessment"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
