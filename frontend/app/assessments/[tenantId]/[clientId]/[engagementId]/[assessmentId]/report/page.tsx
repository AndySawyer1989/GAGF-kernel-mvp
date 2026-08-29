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
import { PrintReportButton } from "@/components/print-report-button";
import {
  ReportDeliveryPanel
} from "@/components/report-delivery-panel";
import {
  extractClientReport,
  fetchAssessment,
  fetchAssessmentArtifacts,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentArtifactList,
  type GovernanceAssessmentClientReport,
  type GovernanceAssessmentIdentity,
  type GovernanceAssessmentRecord,
  type GovernanceAssessmentReportSection
} from "@/lib/governance-assessment-api";

function reportErrorMessage(
  caught: unknown
): string {
  if (
    caught instanceof GovernanceAssessmentApiError
  ) {
    if (caught.status === 404) {
      return (
        "The assessment or client report could not be found."
      );
    }

    return (
      `Backend returned ${caught.status} while loading the report.`
    );
  }

  return "The client report could not be loaded.";
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function inlineMarkdown(value: string): React.ReactNode[] {
  const parts = value.split(
    /(\*\*[^*]+\*\*|`[^`]+`)/
  );

  return parts.map((part, index) => {
    if (
      part.startsWith("**") &&
      part.endsWith("**")
    ) {
      return (
        <strong key={`${part}-${index}`}>
          {part.slice(2, -2)}
        </strong>
      );
    }

    if (
      part.startsWith("`") &&
      part.endsWith("`")
    ) {
      return (
        <code key={`${part}-${index}`}>
          {part.slice(1, -1)}
        </code>
      );
    }

    return part;
  });
}

function ReportSectionBody({
  section
}: {
  section: GovernanceAssessmentReportSection;
}) {
  const lines = section.markdown
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const ordered = lines.every(
    (line) => /^\d+\.\s/.test(line)
  );

  const unordered = lines.every(
    (line) => line.startsWith("- ")
  );

  if (ordered) {
    return (
      <ol className="report-list report-ordered-list">
        {lines.map((line) => (
          <li key={line}>
            {inlineMarkdown(
              line.replace(/^\d+\.\s*/, "")
            )}
          </li>
        ))}
      </ol>
    );
  }

  if (unordered) {
    return (
      <ul className="report-list">
        {lines.map((line) => (
          <li key={line}>
            {inlineMarkdown(
              line.replace(/^-\s*/, "")
            )}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="report-paragraphs">
      {lines.map((line) => (
        <p key={line}>
          {inlineMarkdown(line)}
        </p>
      ))}
    </div>
  );
}

export default function ClientReportPage() {
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

  const [artifacts, setArtifacts] =
    useState<GovernanceAssessmentArtifactList | null>(
      null
    );

  const [report, setReport] =
    useState<GovernanceAssessmentClientReport | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadReport = useCallback(
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

        const reportResult =
          extractClientReport(artifactResult);

        if (!reportResult) {
          throw new Error(
            "Client report package missing"
          );
        }

        setAssessment(assessmentResult);
        setArtifacts(artifactResult);
        setReport(reportResult);
      } catch (caught) {
        if (
          caught instanceof DOMException &&
          caught.name === "AbortError"
        ) {
          return;
        }

        setError(reportErrorMessage(caught));
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

    void loadReport(controller.signal);

    return () => controller.abort();
  }, [loadReport]);

  const detailUrl =
    "/assessments/"
    + encodeURIComponent(identity.tenantId)
    + "/"
    + encodeURIComponent(identity.clientId)
    + "/"
    + encodeURIComponent(identity.engagementId)
    + "/"
    + encodeURIComponent(identity.assessmentId);

  const sortedSections =
    report?.sections
      .slice()
      .sort(
        (left, right) =>
          left.order - right.order
      ) ?? [];

  return (
    <main className="console-shell report-console-shell">
      <div className="report-console-navigation">
        <ConsoleSidebar
          activePage="assessments"
          tenantId={config.tenantId}
          actorId={config.actorId}
        />
      </div>

      <section className="workspace report-workspace">
        <header className="topbar report-toolbar">
          <div>
            <p className="eyebrow">
              Client Deliverable
            </p>
            <h1>Governance Assessment Report</h1>
            <p className="page-description">
              Customer-facing executive findings,
              priorities, roadmap, and evidence
              commitments.
            </p>
          </div>

          <div className="topbar-actions">
            <Link
              className="secondary-button button-link"
              href={detailUrl}
            >
              Back to assessment
            </Link>

            <PrintReportButton />
          </div>
        </header>

        {error && (
          <section
            className="error-panel"
            role="alert"
          >
            <div>
              <p className="error-title">
                Client report unavailable
              </p>
              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() => void loadReport()}
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
          artifacts &&
          report && (
            <article className="client-report">
              <header className="client-report-cover">
                <div className="report-brand">
                  <div className="brand-mark">
                    G
                  </div>

                  <div>
                    <p className="brand-name">
                      GAGF
                    </p>
                    <p className="report-brand-subtitle">
                      Friction Intelligence Platform
                    </p>
                  </div>
                </div>

                <div className="report-cover-main">
                  <p className="panel-kicker">
                    Governance Runway Assessment
                  </p>

                  <h2>{report.title}</h2>

                  <p className="report-cover-description">
                    Evidence-governed organizational
                    assessment, intervention priorities,
                    and delivery roadmap.
                  </p>
                </div>

                <dl className="report-cover-metadata">
                  <div>
                    <dt>Client</dt>
                    <dd>{identity.clientId}</dd>
                  </div>

                  <div>
                    <dt>Engagement</dt>
                    <dd>{identity.engagementId}</dd>
                  </div>

                  <div>
                    <dt>Assessment</dt>
                    <dd>{identity.assessmentId}</dd>
                  </div>

                  <div>
                    <dt>Status</dt>
                    <dd>{assessment.status}</dd>
                  </div>

                  <div>
                    <dt>Completed</dt>
                    <dd>
                      {formatDate(
                        assessment.updated_at
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt>Report ID</dt>
                    <dd>{report.report_id}</dd>
                  </div>
                </dl>

                <div className="report-cover-verification">
                  <span className="status-badge status-healthy">
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />
                    Governed report package verified
                  </span>

                  <span>
                    {artifacts.count} evidence-bound
                    artifacts
                  </span>
                </div>
              </header>

              <div className="client-report-body">
                {sortedSections.map((section) => (
                  <section
                    className={
                      section.kind ===
                      "executive-summary"
                        ? "report-section report-section-featured"
                        : "report-section"
                    }
                    key={section.section_id}
                  >
                    <div className="report-section-heading">
                      <span>
                        {String(section.order).padStart(
                          2,
                          "0"
                        )}
                      </span>

                      <div>
                        <p className="panel-kicker">
                          {section.kind.replaceAll(
                            "-",
                            " "
                          )}
                        </p>
                        <h2>{section.title}</h2>
                      </div>
                    </div>

                    <ReportSectionBody
                      section={section}
                    />
                  </section>
                ))}
              </div>

              <footer className="client-report-footer">
                <div>
                  <p>Evidence-governed by GAGF</p>
                  <span>
                    Deterministic assessment authority
                  </span>
                </div>

                <dl>
                  <div>
                    <dt>Package hash</dt>
                    <dd>
                      {report.manifest.package_hash}
                    </dd>
                  </div>

                  <div>
                    <dt>Schema</dt>
                    <dd>
                      {report.manifest.schema_version}
                    </dd>
                  </div>
                </dl>
              </footer>
             <ReportDeliveryPanel
  reportId={report.report_id}
  packageHash={report.manifest.package_hash}
  schemaVersion={report.manifest.schema_version}
/>
            </article>
          )}
      </section>
    </main>
  );
}
