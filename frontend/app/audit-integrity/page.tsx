"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { ConsoleSidebar } from "@/components/console-sidebar";
import {
  createAuditCheckpoint,
  fetchAuditCheckpoints,
  fetchAuditEvents,
  fetchAuditIntegrity,
  fetchSignedAuditCheckpoints,
  getGovernanceAssessmentApiConfig,
  GovernanceAssessmentApiError,
  verifySignedAuditCheckpoints,
  type GovernanceAssessmentAuditEvent,
  type GovernanceAssessmentAuditEventList,
  type GovernanceAssessmentAuditIntegrity,
  type GovernanceAssessmentCheckpointList,
  type GovernanceAssessmentSignedVerification
} from "@/lib/governance-assessment-api";

function formatTimestamp(
  value: string
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit"
  });
}

function shortHash(value: string): string {
  if (value.length <= 20) {
    return value;
  }

  return `${value.slice(0, 10)}?${value.slice(-8)}`;
}

function eventMatches(
  event: GovernanceAssessmentAuditEvent,
  outcome: string
): boolean {
  return (
    outcome === "ALL" ||
    event.outcome.toUpperCase() === outcome
  );
}

export default function AuditIntegrityPage() {
  const config = useMemo(
    () => getGovernanceAssessmentApiConfig(),
    []
  );

  const [events, setEvents] =
    useState<GovernanceAssessmentAuditEventList | null>(
      null
    );

  const [integrity, setIntegrity] =
    useState<GovernanceAssessmentAuditIntegrity | null>(
      null
    );

  const [checkpoints, setCheckpoints] =
    useState<GovernanceAssessmentCheckpointList | null>(
      null
    );

  const [signedCheckpoints, setSignedCheckpoints] =
    useState<GovernanceAssessmentCheckpointList | null>(
      null
    );

  const [signedVerification, setSignedVerification] =
    useState<GovernanceAssessmentSignedVerification | null>(
      null
    );

  const [outcomeFilter, setOutcomeFilter] =
    useState("ALL");

  const [loading, setLoading] =
    useState(true);

  const [creating, setCreating] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [notice, setNotice] =
    useState<string | null>(null);

  const loadAuditConsole = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const [
          eventResult,
          integrityResult,
          checkpointResult,
          signedCheckpointResult,
          signedVerificationResult
        ] = await Promise.all([
          fetchAuditEvents(config, signal),
          fetchAuditIntegrity(config, signal),
          fetchAuditCheckpoints(config, signal),
          fetchSignedAuditCheckpoints(
            config,
            signal
          ),
          verifySignedAuditCheckpoints(
            config,
            signal
          )
        ]);

        setEvents(eventResult);
        setIntegrity(integrityResult);
        setCheckpoints(checkpointResult);
        setSignedCheckpoints(
          signedCheckpointResult
        );
        setSignedVerification(
          signedVerificationResult
        );
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
            `Backend returned ${caught.status} while loading audit integrity data.`
          );
        } else {
          setError(
            "The Audit Integrity Console could not be loaded."
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

    void loadAuditConsole(controller.signal);

    return () => controller.abort();
  }, [loadAuditConsole]);

  async function createCheckpoint() {
    setCreating(true);
    setError(null);
    setNotice(null);

    try {
      await createAuditCheckpoint(config);

      setNotice(
        "A new tenant audit checkpoint was created."
      );

      await loadAuditConsole();
    } catch (caught) {
      if (
        caught instanceof GovernanceAssessmentApiError
      ) {
        setError(
          `Checkpoint creation failed with status ${caught.status}.`
        );
      } else {
        setError(
          "The audit checkpoint could not be created."
        );
      }
    } finally {
      setCreating(false);
    }
  }

  const filteredEvents =
    events?.items.filter((event) =>
      eventMatches(event, outcomeFilter)
    ) ?? [];

  const allowedCount =
    events?.items.filter(
      (event) =>
        event.outcome.toLowerCase() === "allowed"
    ).length ?? 0;

  const deniedCount =
    events?.items.filter(
      (event) =>
        event.outcome.toLowerCase() === "denied"
    ).length ?? 0;

  return (
    <main className="console-shell">
      <ConsoleSidebar
        activePage="audit-integrity"
        tenantId={config.tenantId}
        actorId={config.actorId}
      />

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Constitutional Audit Layer
            </p>
            <h1>Audit Integrity</h1>
            <p className="page-description">
              Verify tenant audit continuity, inspect
              administrative activity, and create
              immutable audit checkpoints.
            </p>
          </div>

          <div className="topbar-actions">
            <button
              className="secondary-button"
              type="button"
              disabled={creating || loading}
              onClick={() =>
                void createCheckpoint()
              }
            >
              {creating
                ? "Creating checkpoint?"
                : "Create checkpoint"}
            </button>

            <button
              className="refresh-button"
              type="button"
              disabled={loading}
              onClick={() =>
                void loadAuditConsole()
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
                Audit console unavailable
              </p>
              <p>{error}</p>
            </div>

            <button
              type="button"
              onClick={() =>
                void loadAuditConsole()
              }
            >
              Retry
            </button>
          </section>
        )}

        {notice && (
          <section
            className="audit-notice"
            aria-live="polite"
          >
            {notice}
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
          events &&
          integrity &&
          checkpoints &&
          signedCheckpoints &&
          signedVerification && (
            <>
              <section className="audit-status-strip">
                <div>
                  <p className="status-heading">
                    Audit chain
                  </p>

                  <span
                    className={
                      integrity.valid
                        ? "status-badge status-healthy"
                        : "status-badge status-warning"
                    }
                  >
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />

                    {integrity.valid
                      ? "Valid"
                      : "Integrity failure"}
                  </span>
                </div>

                <div>
                  <p className="status-heading">
                    Events checked
                  </p>
                  <p className="status-value">
                    {integrity.checked_count}
                  </p>
                </div>

                <div>
                  <p className="status-heading">
                    Signed verification
                  </p>

                  <span
                    className={
                      signedVerification.available
                        ? "status-badge status-healthy"
                        : "status-badge status-warning"
                    }
                  >
                    <span
                      className="status-dot"
                      aria-hidden="true"
                    />

                    {signedVerification.available
                      ? "Available"
                      : "Unavailable"}
                  </span>
                </div>
              </section>

              <section className="result-metrics-grid">
                <article className="result-metric">
                  <p>Audit events</p>
                  <strong>{events.count}</strong>
                  <span>
                    Most recent tenant records
                  </span>
                </article>

                <article className="result-metric">
                  <p>Allowed operations</p>
                  <strong>{allowedCount}</strong>
                  <span>
                    Authorized activity in view
                  </span>
                </article>

                <article className="result-metric">
                  <p>Denied operations</p>
                  <strong>{deniedCount}</strong>
                  <span>
                    Enforced access decisions
                  </span>
                </article>

                <article className="result-metric">
                  <p>Checkpoints</p>
                  <strong>
                    {checkpoints.count}
                  </strong>
                  <span>
                    Recorded integrity anchors
                  </span>
                </article>
              </section>

              {!signedVerification.available && (
                <section className="signed-verifier-warning">
                  <div>
                    <p className="panel-kicker">
                      Signed checkpoint posture
                    </p>
                    <h2>
                      Signature verifier unavailable
                    </h2>
                    <p>
                      {signedVerification.message}
                    </p>
                  </div>

                  <code>
                    {signedVerification.code}
                  </code>
                </section>
              )}

              <section className="audit-grid">
                <article className="panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Audit continuity
                      </p>
                      <h2>Chain verification</h2>
                    </div>

                    <span
                      className={
                        integrity.valid
                          ? "status-badge status-healthy"
                          : "status-badge status-warning"
                      }
                    >
                      {integrity.valid
                        ? "Verified"
                        : "Failed"}
                    </span>
                  </div>

                  <dl className="connection-list">
                    <div>
                      <dt>Tenant</dt>
                      <dd>{integrity.tenant_id}</dd>
                    </div>

                    <div>
                      <dt>Checked events</dt>
                      <dd>
                        {integrity.checked_count}
                      </dd>
                    </div>

                    <div>
                      <dt>Failure index</dt>
                      <dd>
                        {integrity.failure_index ??
                          "None"}
                      </dd>
                    </div>

                    <div>
                      <dt>Failure event</dt>
                      <dd>
                        {integrity.failure_event_id ??
                          "None"}
                      </dd>
                    </div>

                    <div>
                      <dt>Reason code</dt>
                      <dd>
                        {integrity.reason_code ??
                          "None"}
                      </dd>
                    </div>
                  </dl>
                </article>

                <article className="panel">
                  <div className="panel-header">
                    <div>
                      <p className="panel-kicker">
                        Integrity anchors
                      </p>
                      <h2>Checkpoint inventory</h2>
                    </div>

                    <span className="status-value">
                      {checkpoints.count} checkpoint
                      {checkpoints.count === 1
                        ? ""
                        : "s"}
                    </span>
                  </div>

                  {checkpoints.items.length === 0 ? (
                    <div className="audit-empty">
                      No audit checkpoints have been
                      created for this tenant.
                    </div>
                  ) : (
                    <pre className="checkpoint-json">
                      {JSON.stringify(
                        checkpoints.items,
                        null,
                        2
                      )}
                    </pre>
                  )}

                  <div className="signed-checkpoint-count">
                    <span>Signed checkpoints</span>
                    <strong>
                      {signedCheckpoints.count}
                    </strong>
                  </div>
                </article>
              </section>

              <section className="panel audit-event-panel">
                <div className="panel-header">
                  <div>
                    <p className="panel-kicker">
                      Administrative evidence
                    </p>
                    <h2>Tenant audit events</h2>
                  </div>

                  <label className="evidence-filter">
                    <span>Outcome</span>

                    <select
                      value={outcomeFilter}
                      onChange={(event) =>
                        setOutcomeFilter(
                          event.target.value
                        )
                      }
                    >
                      <option value="ALL">
                        All outcomes
                      </option>
                      <option value="ALLOWED">
                        Allowed
                      </option>
                      <option value="DENIED">
                        Denied
                      </option>
                    </select>
                  </label>
                </div>

                <div className="audit-event-table">
                  <div className="audit-event-header">
                    <span>Time</span>
                    <span>Actor</span>
                    <span>Operation</span>
                    <span>Outcome</span>
                    <span>Event hash</span>
                  </div>

                  {filteredEvents.map((event) => (
                    <div
                      className="audit-event-row"
                      key={event.event_id}
                    >
                      <span>
                        {formatTimestamp(
                          event.occurred_at
                        )}
                      </span>

                      <div>
                        <strong>
                          {event.actor_id}
                        </strong>
                        <span>
                          {event.actor_roles.join(", ")}
                        </span>
                      </div>

                      <div>
                        <strong>
                          {event.method}
                          {" "}
                          {event.status_code}
                        </strong>
                        <span title={event.route}>
                          {event.route}
                        </span>
                      </div>

                      <div>
                        <span
                          className={
                            event.outcome === "allowed"
                              ? "status-badge status-healthy"
                              : "status-badge status-warning"
                          }
                        >
                          {event.outcome}
                        </span>

                        {event.reason_code && (
                          <code>
                            {event.reason_code}
                          </code>
                        )}
                      </div>

                      <code
                        title={event.event_hash}
                      >
                        {shortHash(
                          event.event_hash
                        )}
                      </code>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
      </section>
    </main>
  );
}
