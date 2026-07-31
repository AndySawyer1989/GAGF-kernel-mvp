"use client";

import Link from "next/link";

import {
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";
import {
  fetchAssessments,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentListItem,
  type GovernanceAssessmentListResponse
} from "@/lib/governance-assessment-api";

function readString(
  record: GovernanceAssessmentListItem,
  ...keys: string[]
): string | null {
  for (const key of keys) {
    const value = record[key];

    if (
      typeof value === "string" &&
      value.trim().length > 0
    ) {
      return value;
    }
  }

  return null;
}

function formatDate(value: string | null): string {
  if (!value) {
    return "Not recorded";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString([], {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
}

function AssessmentCard({
  assessment
}: {
  assessment: GovernanceAssessmentListItem;
}) {
  const assessmentId =
    readString(assessment, "assessment_id", "id") ??
    "Unidentified assessment";

  const assessmentName =
    readString(
      assessment,
      "assessment_name",
      "name",
      "title"
    ) ?? assessmentId;

  const clientId =
    readString(assessment, "client_id") ??
    "No client recorded";

  const engagementId =
    readString(assessment, "engagement_id") ??
    "No engagement recorded";

  const status =
    readString(
      assessment,
      "status",
      "assessment_status",
      "state"
    ) ?? "Recorded";

  const createdAt = readString(
    assessment,
    "created_at",
    "executed_at",
    "generated_at",
    "timestamp"
  );

  return (
    <article className="assessment-card">
      <div className="assessment-card-header">
        <div>
          <p className="assessment-context">
            {clientId} / {engagementId}
          </p>
          <h2>{assessmentName}</h2>
        </div>

        <span className="assessment-status">
          {status}
        </span>
      </div>

      <dl className="assessment-metadata">
        <div>
          <dt>Assessment ID</dt>
          <dd>{assessmentId}</dd>
        </div>
        <div>
          <dt>Recorded</dt>
          <dd>{formatDate(createdAt)}</dd>
        </div>
      </dl>

      <div className="assessment-card-footer">
        <span>
          Evidence-governed assessment record
        </span>

        <Link
          className="secondary-button button-link"
          href={
            "/assessments/"
            + encodeURIComponent(
                String(assessment.tenant_id)
              )
            + "/"
            + encodeURIComponent(
                String(assessment.client_id)
              )
            + "/"
            + encodeURIComponent(
                String(assessment.engagement_id)
              )
            + "/"
            + encodeURIComponent(
                String(assessment.assessment_id)
              )
          }
        >
          Open assessment
        </Link>
      </div>
    </article>
  );
}

export default function AssessmentsPage() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [response, setResponse] =
    useState<GovernanceAssessmentListResponse>({
      items: [],
      count: 0
    });

  const [clientId, setClientId] = useState("");
  const [engagementId, setEngagementId] =
    useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(
    null
  );

  const loadAssessments = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchAssessments(
          config,
          {
            clientId,
            engagementId
          },
          signal
        );

        setResponse(result);
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
            `Backend returned ${caught.status}. Verify the tenant and assessment permissions.`
          );
        } else {
          setError(
            "The assessment collection could not be loaded."
          );
        }
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [clientId, config, engagementId]
  );

  useEffect(() => {
    const controller = new AbortController();

    void loadAssessments(controller.signal);

    return () => controller.abort();
  }, [loadAssessments]);

  const filtersActive =
    clientId.trim().length > 0 ||
    engagementId.trim().length > 0;

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="assessments"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Governance Assessment
            </p>
            <h1>Assessments</h1>
            <p className="page-description">
              Browse tenant-scoped assessment records,
              organizational context, and evidence-governed
              outcomes.
            </p>
          </div>

          <div className="topbar-actions">
            <p className="collection-count">
              {loading
                ? "Loading records"
                : `${response.count} assessment${
                    response.count === 1 ? "" : "s"
                  }`}
            </p>

            <button
              className="refresh-button"
              type="button"
              disabled={loading}
              onClick={() => void loadAssessments()}
            >
              {loading ? "Refreshing?" : "Refresh"}
            </button>
          </div>
        </header>

        <section
          className="assessment-filters"
          aria-label="Assessment filters"
        >
          <label>
            <span>Client ID</span>
            <input
              type="text"
              value={clientId}
              placeholder="Filter by client"
              onChange={(event) =>
                setClientId(event.target.value)
              }
            />
          </label>

          <label>
            <span>Engagement ID</span>
            <input
              type="text"
              value={engagementId}
              placeholder="Filter by engagement"
              onChange={(event) =>
                setEngagementId(event.target.value)
              }
            />
          </label>

          <button
            className="secondary-button"
            type="button"
            disabled={!filtersActive}
            onClick={() => {
              setClientId("");
              setEngagementId("");
            }}
          >
            Clear filters
          </button>
        </section>

        {error && (
          <section className="error-panel" role="alert">
            <div>
              <p className="error-title">
                Assessments unavailable
              </p>
              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() => void loadAssessments()}
            >
              Retry
            </button>
          </section>
        )}

        {!error && loading && (
          <section
            className="assessment-loading"
            aria-live="polite"
          >
            <div className="loading-pulse" />
            <div className="loading-pulse" />
            <div className="loading-pulse" />
          </section>
        )}

        {!error &&
          !loading &&
          response.items.length === 0 && (
            <section className="assessment-empty">
              <div className="empty-symbol">?</div>

              <p className="panel-kicker">
                Assessment runway
              </p>

              <h2>
                {filtersActive
                  ? "No assessments match these filters"
                  : "No assessments have been executed"}
              </h2>

              <p>
                {filtersActive
                  ? "Clear the filters or enter another client and engagement context."
                  : "The tenant is ready. The next step is to execute its first evidence-governed assessment."}
              </p>

              {filtersActive ? (
                <button
                  className="refresh-button"
                  type="button"
                  onClick={() => {
                    setClientId("");
                    setEngagementId("");
                  }}
                >
                  Clear filters
                </button>
              ) : (
                <Link
                  className="refresh-button button-link"
                  href="/assessments/new"
                >
                  Execute first assessment
                </Link>
              )}
            </section>
          )}

        {!error &&
          !loading &&
          response.items.length > 0 && (
            <section className="assessment-list">
              {response.items.map(
                (assessment, index) => (
                  <AssessmentCard
                    key={
                      readString(
                        assessment,
                        "assessment_id",
                        "id"
                      ) ?? `assessment-${index}`
                    }
                    assessment={assessment}
                  />
                )
              )}
            </section>
          )}
      </section>
    </main>
  );
}
