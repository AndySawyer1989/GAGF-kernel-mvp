"use client";

import Link from "next/link";
import {
  useParams,
  useSearchParams
} from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";
import {
  fetchAssessment,
  fetchAssessmentArtifacts,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentArtifact,
  type GovernanceAssessmentArtifactList,
  type GovernanceAssessmentIdentity,
  type GovernanceAssessmentRecord
} from "@/lib/governance-assessment-api";

type JsonObject = Record<string, unknown>;

type EvidenceRecord = {
  event_id: string;
  event_type: string;
  occurred_at: string;
  work_item_id: string | null;
  source_id: string;
  evidence_hash: string;
  row_number: number;
};

type EvidenceSourceSummary = {
  source_id: string;
  display_name: string;
  source_kind: string;
  total_rows: number;
  accepted_rows: number;
  rejected_rows: number;
  acceptance_rate: number;
  valid: boolean;
  intake_hash: string;
};

function isObject(
  value: unknown
): value is JsonObject {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function stringValue(
  value: unknown,
  fallback = ""
): string {
  return typeof value === "string"
    ? value
    : fallback;
}

function numberValue(
  value: unknown,
  fallback = 0
): number {
  return typeof value === "number"
    ? value
    : fallback;
}

function booleanValue(
  value: unknown,
  fallback = false
): boolean {
  return typeof value === "boolean"
    ? value
    : fallback;
}

function objectArray(
  value: unknown
): JsonObject[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isObject);
}

function artifactByType(
  artifacts: GovernanceAssessmentArtifactList | null,
  artifactType: string
): GovernanceAssessmentArtifact | undefined {
  return artifacts?.items.find(
    (artifact) =>
      artifact.artifact_type === artifactType
  );
}

function parseEvidenceRecords(
  intakeArtifact:
    GovernanceAssessmentArtifact | undefined
): EvidenceRecord[] {
  if (!intakeArtifact) {
    return [];
  }

  const intakeResults = objectArray(
    intakeArtifact.payload.intake_results
  );

  return intakeResults.flatMap(
    (result) =>
      objectArray(result.accepted_records).map(
        (record) => {
          const attributes = isObject(
            record.attributes
          )
            ? record.attributes
            : {};

          return {
            event_id: stringValue(
              record.event_id,
              "unknown-event"
            ),
            event_type: stringValue(
              record.event_type,
              "UNKNOWN"
            ),
            occurred_at: stringValue(
              record.occurred_at
            ),
            work_item_id:
              typeof attributes.work_item_id ===
              "string"
                ? attributes.work_item_id
                : null,
            source_id: stringValue(
              record.source_id,
              "unknown-source"
            ),
            evidence_hash: stringValue(
              record.evidence_hash
            ),
            row_number: numberValue(
              record.row_number
            )
          };
        }
      )
  );
}

function parseSourceSummaries(
  qualityArtifact:
    GovernanceAssessmentArtifact | undefined
): EvidenceSourceSummary[] {
  if (!qualityArtifact) {
    return [];
  }

  return objectArray(
    qualityArtifact.payload.source_summaries
  ).map((source) => ({
    source_id: stringValue(
      source.source_id,
      "unknown-source"
    ),
    display_name: stringValue(
      source.display_name,
      "Unnamed source"
    ),
    source_kind: stringValue(
      source.source_kind,
      "unknown"
    ),
    total_rows: numberValue(
      source.total_rows
    ),
    accepted_rows: numberValue(
      source.accepted_rows
    ),
    rejected_rows: numberValue(
      source.rejected_rows
    ),
    acceptance_rate: numberValue(
      source.acceptance_rate
    ),
    valid: booleanValue(source.valid),
    intake_hash: stringValue(
      source.intake_hash
    )
  }));
}

function formatTimestamp(
  value: string
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value || "Not recorded";
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function shortHash(value: string): string {
  if (value.length <= 18) {
    return value;
  }

  return `${value.slice(0, 10)}?${value.slice(-8)}`;
}

export default function AssessmentEvidencePage() {
  const params = useParams<{
    tenantId: string;
    clientId: string;
    engagementId: string;
    assessmentId: string;
  }>();

  const searchParams = useSearchParams();

  const requestedConstraint =
  searchParams.get("constraint")?.trim() ?? "";

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

  const [artifacts, setArtifacts] =
    useState<GovernanceAssessmentArtifactList | null>(
      null
    );

  const [selectedEventType, setSelectedEventType] =
    useState("ALL");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadEvidence = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const [
          assessmentResult,
          artifactResult
        ] = await Promise.all([
          fetchAssessment(
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
            `Backend returned ${caught.status} while loading assessment evidence.`
          );
        } else {
          setError(
            "Assessment evidence could not be loaded."
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

    void loadEvidence(controller.signal);

    return () => controller.abort();
  }, [loadEvidence]);

  const intakeArtifact = artifactByType(
    artifacts,
    "evidence-intake-batch"
  );

  const qualityArtifact = artifactByType(
    artifacts,
    "evidence-quality"
  );

  const evidenceRecords = useMemo(
    () =>
      parseEvidenceRecords(intakeArtifact),
    [intakeArtifact]
  );

  const sourceSummaries = useMemo(
    () =>
      parseSourceSummaries(qualityArtifact),
    [qualityArtifact]
  );

  const eventTypes = useMemo(
    () => [
      "ALL",
      ...Array.from(
        new Set(
          evidenceRecords.map(
            (record) => record.event_type
          )
        )
      ).sort()
    ],
    [evidenceRecords]
  );


  useEffect(() => {
    if (!requestedConstraint) {
      return;
    }

    if (
      eventTypes.includes(
        requestedConstraint
      )
    ) {
      setSelectedEventType(
        requestedConstraint
      );
    }
  }, [
    eventTypes,
    requestedConstraint
  ]);

  const filteredRecords = useMemo(
    () =>
      selectedEventType === "ALL"
        ? evidenceRecords
        : evidenceRecords.filter(
            (record) =>
              record.event_type ===
              selectedEventType
          ),
    [
      evidenceRecords,
      selectedEventType
    ]
  );

  const acceptedRows = numberValue(
    qualityArtifact?.payload.accepted_rows
  );

  const rejectedRows = numberValue(
    qualityArtifact?.payload.rejected_rows
  );

  const qualityScore = numberValue(
    qualityArtifact?.payload.quality_score
  );

  const qualityGrade = stringValue(
    qualityArtifact?.payload.quality_grade,
    "unknown"
  );

  const coverageRate = numberValue(
    qualityArtifact?.payload
      .requirement_coverage_rate
  );

  const readyForAnalysis = booleanValue(
    qualityArtifact?.payload
      .ready_for_analysis
  );

  const assessmentUrl = [
    "/assessments",
    encodeURIComponent(identity.tenantId),
    encodeURIComponent(identity.clientId),
    encodeURIComponent(identity.engagementId),
    encodeURIComponent(identity.assessmentId)
  ].join("/");

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="evidence"
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
              Evidence Constitution
            </p>

            <h1>
              {assessment?.assessment_name ??
                "Assessment Evidence"}
            </h1>

            <p className="page-description">
              {identity.clientId}
              {" / "}
              {identity.engagementId}
              {" / "}
              {identity.assessmentId}
            </p>
          </div>

          <div className="topbar-actions">
            <Link
              className="secondary-button button-link"
              href="/evidence"
            >
              Back to evidence
            </Link>

            <Link
              className="secondary-button button-link"
              href={assessmentUrl}
            >
              View assessment
            </Link>

            <button
              className="refresh-button"
              type="button"
              disabled={loading}
              onClick={() =>
                void loadEvidence()
              }
            >
              {loading
                ? "Refreshing?"
                : "Refresh"}
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
                Evidence unavailable
              </p>

              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() =>
                void loadEvidence()
              }
            >
              Retry
            </button>
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
          artifacts && (
            <>
              <section className="evidence-status-strip">
                <div>
                  <p className="status-heading">
                    Evidence status
                  </p>

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
                      ? "Ready for analysis"
                      : "Review required"}
                  </span>
                </div>

                <div>
                  <p className="status-heading">
                    Quality grade
                  </p>

                  <p className="status-value">
                    {qualityGrade}
                  </p>
                </div>

                <div>
                  <p className="status-heading">
                    Intake chain
                  </p>

                  <span className="status-badge status-healthy">
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />

                    Verified
                  </span>
                </div>
              </section>

              <section className="result-metrics-grid">
                <article className="result-metric">
                  <p>Accepted records</p>

                  <strong>
                    {acceptedRows}
                  </strong>

                  <span>
                    Governed evidence events
                  </span>
                </article>

                <article className="result-metric">
                  <p>Rejected records</p>

                  <strong>
                    {rejectedRows}
                  </strong>

                  <span>
                    Failed intake validation
                  </span>
                </article>

                <article className="result-metric">
                  <p>Quality score</p>

                  <strong>
                    {qualityScore.toFixed(2)}
                  </strong>

                  <span>
                    {qualityGrade} evidence
                  </span>
                </article>

                <article className="result-metric">
                  <p>Requirement coverage</p>

                  <strong>
                    {(coverageRate * 100).toFixed(
                      0
                    )}
                    %
                  </strong>

                  <span>
                    Configured commitments met
                  </span>
                </article>
              </section>

              <section className="panel evidence-source-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Evidence sources
                    </p>

                    <h2>
                      Source commitments
                    </h2>
                  </div>

                  <span className="status-value">
                    {sourceSummaries.length} source
                    {sourceSummaries.length === 1
                      ? ""
                      : "s"}
                  </span>
                </div>

                <div className="evidence-source-grid">
                  {sourceSummaries.map(
                    (source) => (
                      <article
                        className="evidence-source-card"
                        key={source.source_id}
                      >
                        <div className="panel-header">
                          <div>
                            <p className="assessment-context">
                              {source.source_kind}
                            </p>

                            <h3>
                              {source.display_name}
                            </h3>
                          </div>

                          <span
                            className={
                              source.valid
                                ? "status-badge status-healthy"
                                : "status-badge status-warning"
                            }
                          >
                            {source.valid
                              ? "Valid"
                              : "Review"}
                          </span>
                        </div>

                        <dl>
                          <div>
                            <dt>
                              Source ID
                            </dt>

                            <dd>
                              {source.source_id}
                            </dd>
                          </div>

                          <div>
                            <dt>
                              Total rows
                            </dt>

                            <dd>
                              {source.total_rows}
                            </dd>
                          </div>

                          <div>
                            <dt>
                              Accepted
                            </dt>

                            <dd>
                              {
                                source.accepted_rows
                              }
                            </dd>
                          </div>

                          <div>
                            <dt>
                              Acceptance
                            </dt>

                            <dd>
                              {(
                                source.acceptance_rate *
                                100
                              ).toFixed(0)}
                              %
                            </dd>
                          </div>
                        </dl>

                        <div className="evidence-hash">
                          <span>
                            Intake hash
                          </span>

                          <code
                            title={
                              source.intake_hash
                            }
                          >
                            {shortHash(
                              source.intake_hash
                            )}
                          </code>
                        </div>
                      </article>
                    )
                  )}
                </div>
              </section>

              {requestedConstraint &&
                selectedEventType ===
                  requestedConstraint && (
                  <section className="evidence-traceability-notice">
                    <div>
                      <p className="panel-kicker">
                        Diagnostic traceability
                      </p>

                      <h2>
                        Supporting evidence for{" "}
                        {
                          requestedConstraint
                        }
                      </h2>

                      <p>
                        This view is filtered
                        to accepted evidence
                        records carrying the
                        selected governed
                        constraint category.
                        Matching evidence
                        supports the diagnostic
                        observation but does
                        not independently
                        establish root cause,
                        causality, or
                        intervention authority.
                      </p>
                    </div>

                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() =>
                        setSelectedEventType(
                          "ALL"
                        )
                      }
                    >
                      Show all evidence
                    </button>
                  </section>
                )}

              <section className="panel evidence-record-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Accepted evidence
                    </p>

                    <h2>
                      Governed event records
                    </h2>
                  </div>

                  <label className="evidence-filter">
                    <span>
                      Constraint category
                    </span>

                    <select
                      value={
                        selectedEventType
                      }
                      onChange={(event) =>
                        setSelectedEventType(
                          event.target.value
                        )
                      }
                    >
                      {eventTypes.map(
                        (eventType) => (
                          <option
                            value={
                              eventType
                            }
                            key={eventType}
                          >
                            {eventType ===
                            "ALL"
                              ? "All categories"
                              : eventType}
                          </option>
                        )
                      )}
                    </select>
                  </label>
                </div>

                <div className="evidence-record-table">
                  <div className="evidence-record-header">
                    <span>
                      Event
                    </span>

                    <span>
                      Constraint
                    </span>

                    <span>
                      Work item
                    </span>

                    <span>
                      Occurred
                    </span>

                    <span>
                      Evidence hash
                    </span>
                  </div>

                  {filteredRecords.map(
                    (record) => (
                      <div
                        className="evidence-record-row"
                        key={
                          record.evidence_hash
                        }
                      >
                        <div>
                          <strong>
                            {
                              record.event_id
                            }
                          </strong>

                          <span>
                            Row{" "}
                            {
                              record.row_number
                            }
                          </span>
                        </div>

                        <span className="constraint-badge">
                          {
                            record.event_type
                          }
                        </span>

                        <span>
                          {record.work_item_id ??
                            "Not recorded"}
                        </span>

                        <span>
                          {formatTimestamp(
                            record.occurred_at
                          )}
                        </span>

                        <code
                          title={
                            record.evidence_hash
                          }
                        >
                          {shortHash(
                            record.evidence_hash
                          )}
                        </code>
                      </div>
                    )
                  )}
                </div>

                {filteredRecords.length ===
                  0 && (
                  <div className="evidence-no-results">
                    No evidence records
                    match this category.
                  </div>
                )}
              </section>
            </>
          )}
      </section>
    </main>
  );
}
