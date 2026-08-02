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
  type GovernanceAssessmentListResponse,
  type GovernanceAssessmentRecord
} from "@/lib/governance-assessment-api";

function evidenceUrl(
  assessment: GovernanceAssessmentRecord
): string {
  return [
    "/evidence",
    encodeURIComponent(assessment.tenant_id),
    encodeURIComponent(assessment.client_id),
    encodeURIComponent(assessment.engagement_id),
    encodeURIComponent(assessment.assessment_id)
  ].join("/");
}

function formatDate(value: string): string {
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

export default function EvidencePage() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [response, setResponse] =
    useState<GovernanceAssessmentListResponse>({
      items: [],
      count: 0
    });

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadAssessments = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchAssessments(
          config,
          {},
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
            `Backend returned ${caught.status} while loading evidence contexts.`
          );
        } else {
          setError(
            "Evidence assessment contexts could not be loaded."
          );
        }
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [config]
  );

  useEffect(() => {
    const controller = new AbortController();

    void loadAssessments(controller.signal);

    return () => controller.abort();
  }, [loadAssessments]);

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="evidence"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace" id="console-main-content" tabIndex={-1}>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Evidence Constitution
            </p>
            <h1>Evidence Explorer</h1>
            <p className="page-description">
              Trace assessment findings to accepted
              evidence events, source commitments, and
              cryptographic evidence records.
            </p>
          </div>

          <div className="topbar-actions">
            <p className="collection-count">
              {loading
                ? "Loading contexts"
                : `${response.count} assessment${
                    response.count === 1 ? "" : "s"
                  }`}
            </p>

            <button
              className="refresh-button"
              type="button"
              disabled={loading}
              onClick={() =>
                void loadAssessments()
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
                Evidence contexts unavailable
              </p>
              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() =>
                void loadAssessments()
              }
            >
              Retry
            </button>
          </section>
        )}

        {!error && loading && (
          <section className="evidence-context-loading">
            <div className="loading-pulse" />
            <div className="loading-pulse" />
          </section>
        )}

        {!error &&
          !loading &&
          response.items.length === 0 && (
            <section className="assessment-empty">
              <div className="empty-symbol">
                E
              </div>

              <p className="panel-kicker">
                Evidence runway
              </p>

              <h2>
                No assessment evidence is available
              </h2>

              <p>
                Execute an assessment before exploring
                governed evidence and source records.
              </p>

              <Link
                className="refresh-button button-link"
                href="/assessments/new"
              >
                Execute assessment
              </Link>
            </section>
          )}

        {!error &&
          !loading &&
          response.items.length > 0 && (
            <section className="evidence-context-list">
              {response.items.map(
                (assessment) => (
                  <article
                    className="evidence-context-card"
                    key={[
                      assessment.tenant_id,
                      assessment.client_id,
                      assessment.engagement_id,
                      assessment.assessment_id
                    ].join("/")}
                  >
                    <div>
                      <p className="assessment-context">
                        {assessment.client_id}
                        {" / "}
                        {assessment.engagement_id}
                      </p>

                      <h2>
                        {assessment.assessment_name}
                      </h2>

                      <p className="evidence-context-description">
                        Explore accepted records, evidence
                        quality, requirement coverage, and
                        cryptographic lineage.
                      </p>
                    </div>

                    <dl className="evidence-context-metadata">
                      <div>
                        <dt>Assessment</dt>
                        <dd>
                          {assessment.assessment_id}
                        </dd>
                      </div>

                      <div>
                        <dt>Status</dt>
                        <dd>{assessment.status}</dd>
                      </div>

                      <div>
                        <dt>Recorded</dt>
                        <dd>
                          {formatDate(
                            assessment.created_at
                          )}
                        </dd>
                      </div>
                    </dl>

                    <Link
                      className="refresh-button button-link"
                      href={evidenceUrl(assessment)}
                    >
                      Explore evidence
                    </Link>
                  </article>
                )
              )}
            </section>
          )}
      </section>
    </main>
  );
}
