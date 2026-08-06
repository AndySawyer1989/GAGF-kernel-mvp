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
  fetchAssessment,
  fetchAssessmentArtifacts,
  fetchAssessmentSummary,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
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

  const executiveSummary =
    textValue(
      projectionArtifact?.payload,
      "executive_summary"
    );

  const findings = stringArray(
    projectionArtifact?.payload,
    "key_findings"
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

const clientReportReady = Boolean(
  findArtifact(
    artifacts,
    CLIENT_REPORT_ARTIFACT_TYPE
  )
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

              <section className="detail-content-grid">
                <article className="panel executive-results-panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Executive projection
                      </p>
                      <h2>Assessment conclusion</h2>
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

                  <div className="dominant-constraint">
                    <span>
                      Dominant constraint
                    </span>
                    <strong>
                      {dominantConstraint}
                    </strong>
                  </div>

                  <div className="result-findings">
                    <h3>Key findings</h3>

                    {findings.map((finding) => (
                      <div key={finding}>
                        <span
                          className="finding-check"
                          aria-hidden="true"
                        />
                        <p>{finding}</p>
                      </div>
                    ))}
                  </div>
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
                            {" ? "}
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
